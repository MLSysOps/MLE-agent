import ast

from agent.hub.utils import match_plan
from agent.integration import read_csv_file
from agent.types import Plan
from agent.utils import *
from .base import BaseAgent
from .code_gen_agent import CodeAgent
from .launch_agent import SetupAgent
from .plan_agent import (
    plan_generator,
    analyze_requirement,
    gen_file_name,
    pmpt_dataset_detect,
    pmpt_task_select,
    pmpt_model_select
)

config = Config()


class LeaderAgent(BaseAgent):
    def __init__(self, project: Project, model):
        """
        LeaderAgent: the interactive chain of the current ML task.
        :param project: the current working project.
        :param model: the language model.
        """
        super().__init__(model, project)

        # if the project is not set up, then raise an error.
        if config.read().get('project') is None:
            self.console.log("You have not set up a project yet.")
            self.console.log("Please create a new project first using 'mle new project_name' command then try again.")
            raise SystemExit

        self.entry_file = self.project.entry_file
        # initialize the plan if it is not set up.
        if self.project.plan is None:
            self.project.plan = Plan(current_task=0)

    def user_requirement_understanding(self):
        """
        (STEP-0) User Requirement Understanding.
        :return:
        """
        if self.project.requirement:
            self.console.print(f"[cyan]User Requirement:[/cyan] {self.project.requirement}")
        else:
            show_panel("STEP 0: User Requirements Understanding")
            self.requirement = questionary.text("Hi, what are your requirements?").ask()
            self.project.requirement = self.requirement

        if not self.requirement:
            raise SystemExit("The user requirement is not provided.")

        # Generate entry file name based on requirement
        self.project.enhanced_requirement = self.requirement
        if self.entry_file is None:
            self.entry_file = gen_file_name(self.project, self.model)
        self.console.print(f"[cyan]Entry File:[/cyan] {self.entry_file}")
        update_project_state(self.project)

    def dataset_selection(self):
        """
        (STEP-1) Dataset Selection.
        :return:
        """

        if self.project.plan.data_kind is None and self.project.plan.dataset is None:
            show_panel("STEP 1: Dataset Selection")
            self.project.plan.data_kind = analyze_requirement(
                self.project.enhanced_requirement,
                pmpt_dataset_detect(),
                self.model
            )

            if self.project.plan.data_kind == 'no_data_information_provided':
                public_dataset_list = analyze_requirement(
                    self.project.enhanced_requirement,
                    pmpt_public_dataset_guess(),
                    self.model
                )
                public_dataset_list = ast.literal_eval(public_dataset_list)
                self.project.plan.dataset = questionary.select(
                    "Please select the dataset:",
                    choices=public_dataset_list
                ).ask()
            elif self.project.plan.data_kind == 'csv_data':
                self.project.plan.dataset = questionary.text("Please provide the CSV data path:").ask()
                if os.path.exists(self.project.plan.dataset) is False:
                    public_dataset_list = analyze_requirement(
                        self.project.enhanced_requirement,
                        pmpt_public_dataset_guess(),
                        self.model
                    )
                    public_dataset_list = ast.literal_eval(public_dataset_list)
                    self.project.plan.dataset = questionary.select(
                        "Please select the dataset:",
                        choices=public_dataset_list
                    ).ask()

        if self.project.plan.dataset is None:
            raise SystemExit("There is no dataset information. Aborted.")
        else:
            self.console.print(f"[cyan]Data Source:[/cyan] {self.project.plan.dataset}")
            if self.project.plan.data_kind == 'csv_data':
                csv_data_sample = read_csv_file(self.project.plan.dataset)
                self.console.print(f"[cyan]Dataset examples:[/cyan]")
                display_dataframe(csv_data_sample)
                self.project.enhanced_requirement += f"\nDataset Sample: {csv_data_sample}"

            self.project.enhanced_requirement += f"\nDataset: {self.project.plan.dataset}"
            update_project_state(self.project)

    def task_model_selection(self):
        """
        (STEP-2) Task & Model Selection.
        :return:
        """
        if self.project.plan.ml_task_type is None or self.project.plan.ml_model_arch is None:
            show_panel("STEP 2: Task & Model Selection")

        # select the ml task type
        if self.project.plan.ml_task_type is None:
            ml_task_list = analyze_requirement(self.project.enhanced_requirement, pmpt_task_select(), self.model)
            ml_task_list = ast.literal_eval(ml_task_list)
            ml_task_type = questionary.select(
                "Please select the ML task type:",
                choices=ml_task_list
            ).ask()

            self.console.log(f"[cyan]ML task type detected:[/cyan] {ml_task_type}")

            self.project.plan.ml_task_type = ml_task_type
            self.project.enhanced_requirement += f"\n\nML task type: {self.project.plan.ml_task_type}"
        else:
            self.console.print(f"[cyan]ML Task:[/cyan] {self.project.plan.ml_task_type}")

        # select the mode architecture
        if self.project.plan.ml_model_arch is None:
            ml_model_list = analyze_requirement(self.project.enhanced_requirement, pmpt_model_select(), self.model)
            ml_model_list = ast.literal_eval(ml_model_list)
            ml_model_arch = questionary.select(
                "Please select the ML model architecture:",
                choices=ml_model_list
            ).ask()
            self.console.log(f"[cyan]Model architecture detected:[/cyan] {ml_model_arch}")

            self.project.plan.ml_model_arch = ml_model_arch
            self.project.enhanced_requirement += f"\nModel architecture: {self.project.plan.ml_model_arch}"
        else:
            self.console.print(f"[cyan]Model Architecture:[/cyan] {self.project.plan.ml_model_arch}")

        update_project_state(self.project)

    def task_planning(self):
        """
        (STEP-3) Task Planning.
        :return:
        """
        if self.project.plan.tasks is None:
            show_panel("STEP 3: Task Planning")
            self.console.log(
                f"The project [cyan]{self.project.name}[/cyan] has no existing plans. "
            )
            self.project.enhanced_requirement += f"\nDataset: {self.project.plan.dataset}"
            with self.console.status("Planning the tasks for you..."):
                task_dicts = plan_generator(self.project.enhanced_requirement, self.model)
                self.console.print(generate_plan_card_ascii(task_dicts), highlight=False)
                self.project.plan.tasks = []
                for task_dict in task_dicts.get('tasks'):
                    task = match_plan(task_dict)
                    if task:
                        self.project.plan.tasks.append(task)

            # Confirm the plan
            confirm_plan = questionary.confirm("Are you sure to use this plan?").ask()
            if confirm_plan:
                update_project_state(self.project)
            else:
                self.console.log("")
                raise SystemExit("Seems you are not satisfied with the plan. Aborting the agent")
        else:
            tasks = []
            for t in self.project.plan.tasks:
                tasks.append({'name': t.name, 'resources': [r.name for r in t.resources], 'description': t.description})
            self.console.print(f"[cyan]Tasks:[/cyan]")
            self.console.print(generate_plan_card_ascii({'tasks': tasks}), highlight=False)

    def code_generation(self):
        """
        (STEP-4) Code Generation.
        :return:
        """
        task_num = len(self.project.plan.tasks)
        if self.project.plan.current_task < task_num:
            show_panel("STEP 4: Code Generation")
            code_generation_agent = CodeAgent(self.model, self.project)
            code_generation_agent.invoke(task_num, self.requirement)
            update_project_state(self.project)

    def execution_and_reflection(self):
        """
        (STEP-5) Execution and Reflection.
        :return:
        """
        show_panel("STEP 5: Execution and Reflection")
        launch_agent = SetupAgent(self.model, self.project)
        launch_agent.invoke()
        update_project_state(self.project)

    def invoke(self):
        """
        Execute the chain.
        :return: the result of the chain.
        """
        try:
            # STEP 0: User Requirement Understanding
            self.user_requirement_understanding()
            # STEP 1: Dataset Selection
            self.dataset_selection()
            # STEP 2: Task & Model Selection
            self.task_model_selection()
            # STEP 3: Task Planning
            self.task_planning()
            # STEP 4: Code Generation
            self.code_generation()
            # STEP 5: Execution and Reflection
            self.execution_and_reflection()
            self.console.log("The chain has been completed.")
        except KeyboardInterrupt:
            self.console.log("MLE Plan Agent has been interrupted.")
            return
