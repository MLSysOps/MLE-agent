import ast

import questionary
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.hub.utils import match_plan
from agent.integration import read_csv_file
from agent.types import Plan
from agent.utils import *
from .code_gen_agent import CodeAgent
from .plan_agent import plan_generator, analyze_requirement, gen_file_name, pmpt_dataset_detect, pmpt_task_select, \
    pmpt_model_select
from .launch_agent import SetupAgent

config = Config()


class LeaderAgent:
    def __init__(self, project: Project, model):
        """
        LeaderAgent: the interactive chain of the current ML task.
        :param project: the current working project.
        :param model: the language model.
        """
        self.project = project
        self.model = model
        self.chat_history = []
        self.console = Console()
        # if the project is not set up, then raise an error.
        if config.read().get('project') is None:
            self.console.log("You have not set up a project yet.")
            self.console.log("Please create a new project first using 'mle new project_name' command then try again.")
            raise SystemExit

        self.project_home = config.read().get('project')['path']
        self.session = PromptSession(
            history=FileHistory(str(os.path.join(self.project_home, CONFIG_TASK_HISTORY_FILE)))
        )

        self.entry_file = self.project.entry_file
        self.requirement = self.project.requirement
        # initialize the plan if it is not set up.
        if self.project.plan is None:
            self.project.plan = Plan(current_task=0)

    def start(self):
        """
        Execute the chain.
        :return: the result of the chain.
        """
        try:
            is_running = True
            while is_running:
                self.console.log("[bold red]Step 1: User requirements understanding[bold red]")
                if self.project.requirement:
                    self.console.log(f"[cyan]User Requirement:[/cyan] {self.project.requirement}")
                else:
                    self.requirement = questionary.text("Hi, what are your requirements?").ask()
                    self.project.requirement = self.requirement

                if not self.requirement:
                    raise SystemExit("The user requirement is not provided.")

                # Generate entry file name based on requirement
                if self.entry_file is None:
                    self.entry_file = gen_file_name(self.project, self.model)
                self.console.log(f"The entry file is: {self.entry_file}")

                self.console.log("[bold red]Step 2: Data quick review[bold red]")
                if self.project.plan.data_kind is None and self.project.plan.dataset is None:
                    self.project.plan.data_kind = analyze_requirement(self.requirement, pmpt_dataset_detect(),
                                                                      self.model)
                    if self.project.plan.data_kind == 'no_data_information_provided':
                        public_dataset_list = analyze_requirement(self.requirement, pmpt_public_dataset_guess(),
                                                                  self.model)
                        public_dataset_list = ast.literal_eval(public_dataset_list)
                        self.project.plan.dataset = questionary.select(
                            "Please select the dataset:",
                            choices=public_dataset_list
                        ).ask()

                    elif self.project.plan.data_kind == 'csv_data':
                        self.project.plan.dataset = questionary.text("Please provide the CSV data path:").ask()
                        # TODO: clean the code
                        if os.path.exists(self.project.plan.dataset) is False:
                            public_dataset_list = analyze_requirement(self.requirement, pmpt_public_dataset_guess(),
                                                                      self.model)
                            public_dataset_list = ast.literal_eval(public_dataset_list)
                            self.project.plan.dataset = questionary.select(
                                "Please select the dataset:",
                                choices=public_dataset_list
                            ).ask()

                if self.project.plan.dataset is None:
                    raise SystemExit("There is no dataset information. Aborted.")
                else:
                    self.console.log(f"[cyan]Data source:[/cyan] {self.project.plan.dataset}")
                    if self.project.plan.data_kind == 'csv_data':
                        csv_data_sample = read_csv_file(self.project.plan.dataset)
                        self.console.log(f"[cyan]Dataset examples:[/cyan] {csv_data_sample}")
                        self.requirement += f"\n\nDataset: {self.project.plan.dataset}"
                        self.requirement += f"\n\nDataset Sample: {csv_data_sample}"
                        update_project_state(self.project)

                self.console.log("[bold red]Step 3: Task & Model selection[bold red]")
                if self.project.plan.ml_task_type is None:
                    ml_task_list = analyze_requirement(self.requirement, pmpt_task_select(), self.model)
                    ml_task_list = ast.literal_eval(ml_task_list)
                    ml_task_type = questionary.select(
                        "Please select the ML task type:",
                        choices=ml_task_list
                    ).ask()
                    self.console.log(f"[cyan]ML task type detected:[/cyan] {ml_task_type}")
                    confirm_ml_task_type = questionary.confirm("Are you sure to use this ml task type?").ask()
                    if confirm_ml_task_type:
                        self.project.plan.ml_task_type = ml_task_type
                        update_project_state(self.project)
                    else:
                        self.console.log("Seems you are not satisfied with the task type. Aborting the chain.")
                        return

                self.requirement += f"\n\nML task type: {self.project.plan.ml_task_type}"
                if self.project.plan.ml_model_arch is None:
                    # TODO: search the best model from kaggle, huggingface, etc
                    ml_model_list = analyze_requirement(self.requirement, pmpt_model_select(), self.model)
                    ml_model_list = ast.literal_eval(ml_model_list)
                    ml_model_arch = questionary.select(
                        "Please select the ML model architecture:",
                        choices=ml_model_list
                    ).ask()
                    self.console.log(f"[cyan]Model architecture detected:[/cyan] {ml_model_arch}")
                    confirm_ml_model_arch = questionary.confirm("Are you sure to use this ml arch?").ask()
                    if confirm_ml_model_arch:
                        self.project.plan.ml_model_arch = ml_model_arch
                        update_project_state(self.project)
                    else:
                        self.console.log("Seems you are not satisfied with the model architecture. Aborting the chain.")
                        return

                self.requirement += f"\n\nModel architecture: {self.project.plan.ml_model_arch}"
                if self.project.plan.tasks is None:
                    self.console.log("[bold red]Step 4: Plan generation[bold red]")
                    self.console.log(
                        f"The project [cyan]{self.project.name}[/cyan] has no existing plans. Start planning..."
                    )
                    self.requirement += f"\n\nDataset: {self.project.plan.dataset}"
                    with self.console.status("Planning the tasks for you..."):
                        task_dicts = plan_generator(
                            self.requirement,
                            self.model,
                        )
                        self.console.log(task_dicts)
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
                        self.console.log("Seems you are not satisfied with the plan. Aborting the chain.")
                        return

                task_num = len(self.project.plan.tasks)
                # check if all tasks are completed.
                # if self.project.plan.current_task == task_num:
                #     self.console.log(":tada: Looks like all tasks are completed.")
                #     return

                # code generation
                self.console.log("[bold red]Step 5: Code generation[bold red]")
                code_generation_agent = CodeAgent(self.model, self.project)
                code_generation_agent.invoke(task_num, self.requirement)

                # install the dependencies for this plan and code.
                self.console.log("[bold red]Step 6: Code execution and reflection [bold red]")
                launch_agent = SetupAgent(self.model, self.project)
                launch_agent.invoke()
                is_running = False
        except KeyboardInterrupt:
            self.console.log("MLE Plan Agent has been interrupted.")
            return
