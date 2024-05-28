import questionary
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.hub.utils import match_plan
from agent.integration import read_csv_file

from agent.utils import *
from agent.utils.prompt import pmpt_chain_filename
from .generator import plan_generator, req_based_generator
from .setup_agent import SetupAgent
from .code_generator import CodeGenerator

config = Config()


class PlanAgent:
    def __init__(self, plan: Plan, llm_agent):
        """
        PlanAgent: the interactive chain of the current ML task.
        :param plan: the plan of the chain.
        :param llm_agent: the language model agent.
        """
        self.plan = plan
        self.agent = llm_agent
        self.chat_history = []
        self.console = Console()
        # if the project is not set up, then raise an error.
        if config.read().get('project') is None:
            self.console.log("You have not set up a project yet.")
            self.console.log("Please create a new project first using 'mle new project_name' command then try again.")
            raise SystemExit

        self.project_home = config.read().get('project')['path']
        self.project_setting_file = os.path.join(self.project_home, CONFIG_PROJECT_FILE)

        self.session = PromptSession(
            history=FileHistory(str(os.path.join(self.project_home, CONFIG_TASK_HISTORY_FILE)))
        )

        self.entry_file = self.plan.entry_file
        self.requirement = self.plan.requirement

    def update_project_state(self):
        """
        Update the project state.
        :return: None
        """
        update_project_plan(self.project_home, self.plan.dict(exclude_none=True))
        return self.plan

    def gen_file_name(self, user_requirement: str):
        """
        Generate a file name.
        :return: the file name.
        """
        self.requirement = user_requirement
        self.chat_history.extend(
            [
                {"role": 'system', "content": pmpt_chain_filename(self.plan.lang)},
                {"role": 'user', "content": self.requirement}
            ]
        )

        with self.console.status("Preparing entry file name..."):
            target_name = extract_file_name(self.agent.query(self.chat_history))
            self.entry_file = str(os.path.join(self.plan.project, target_name))

        self.console.log(f"The entry file is: {self.entry_file}")
        confirm = questionary.confirm("Do you want to use the file?").ask()

        if not confirm:
            new_name = questionary.text("Please provide a new file name:", default=self.entry_file).ask()
            if new_name:
                self.entry_file = new_name
                self.console.log(f"The entry file is: {self.entry_file}")

        # clear the chat history
        self.plan.entry_file = self.entry_file
        self.chat_history = []

        return self.entry_file

    def start(self):
        """
        Execute the chain.
        :return: the result of the chain.
        """
        try:
            is_running = True
            while is_running:
                self.console.log("[bold red]Step 1: User requirements understanding[bold red]")
                if self.plan.requirement:
                    self.console.log(f"[cyan]User Requirement:[/cyan] {self.plan.requirement}")
                else:
                    self.requirement = questionary.text("Hi, what are your requirements?").ask()
                    self.plan.requirement = self.requirement

                if not self.requirement:
                    raise SystemExit("The user requirement is not provided.")

                # Generate entry file name based on requirement
                if self.entry_file is None:
                    self.entry_file = self.gen_file_name(self.requirement)
                    if self.entry_file is None:
                        raise SystemExit("The file name is not generated.")
                    self.console.log(f"Project requirements updated to: {self.project_setting_file}")
                    self.update_project_state()

                self.console.log("[bold red]Step 2: Data quick review[bold red]")
                if self.plan.data_kind is None and self.plan.dataset is None:
                    self.plan.data_kind = req_based_generator(self.requirement, pmpt_dataset_detect(), self.agent)
                    if self.plan.data_kind == 'no_data_information_provided':
                        self.plan.dataset = req_based_generator(self.requirement, pmpt_dataset_select(), self.agent)
                    elif self.plan.data_kind == 'csv_data':
                        self.plan.dataset = questionary.text("Please provide the CSV data path:").ask()
                        if os.path.exists(self.plan.dataset) is False:
                            raise SystemExit("The dataset path is not valid.")

                if self.plan.dataset is None:
                    raise SystemExit("There is no dataset information. Aborted.")
                else:
                    self.console.log(f"[cyan]Data source:[/cyan] {self.plan.dataset}")
                    if self.plan.data_kind == 'csv_data':
                        csv_data_sample = read_csv_file(self.plan.dataset)
                        self.console.log(f"[cyan]Dataset examples:[/cyan] {csv_data_sample}")
                        self.requirement += f"\n\nDataset Sample: {csv_data_sample}"
                        self.update_project_state()

                self.console.log("[bold red]Step 3: Task & Model selection[bold red]")
                if self.plan.ml_task_type is None:
                    ml_task_type = req_based_generator(self.requirement, pmpt_task_select(), self.agent)
                    self.console.log(f"[cyan]ML task type detected:[/cyan] {ml_task_type}")
                    confirm_ml_task_type = questionary.confirm("Are you sure to use this ml task type?").ask()
                    if confirm_ml_task_type:
                        self.plan.ml_task_type = ml_task_type
                        self.update_project_state()
                    else:
                        self.console.log("Seems you are not satisfied with the task type. Aborting the chain.")
                        return

                self.requirement += f"\n\nML task type: {self.plan.ml_task_type}"

                if self.plan.ml_model_arch is None:
                    # TODO: search the best model from kaggle, huggingface, etc
                    ml_model_arch = req_based_generator(self.requirement, pmpt_model_select(), self.agent)
                    self.console.log(f"[cyan]Model architecture detected:[/cyan] {ml_model_arch}")
                    confirm_ml_model_arch = questionary.confirm("Are you sure to use this ml arch?").ask()
                    if confirm_ml_model_arch:
                        self.plan.ml_model_arch = ml_model_arch
                        self.update_project_state()
                    else:
                        self.console.log("Seems you are not satisfied with the model architecture. Aborting the chain.")
                        return

                self.requirement += f"\n\nModel architecture: {self.plan.ml_model_arch}"

                if self.plan.tasks is None:
                    self.console.log("[bold red]Step 4: Plan generation[bold red]")
                    self.console.log(
                        f"The project [cyan]{self.plan.project_name}[/cyan] has no existing plans. Start planning...")
                    self.requirement += f"\n\nDataset: {self.plan.dataset}"
                    with self.console.status("Planning the tasks for you..."):
                        task_dicts = plan_generator(
                            self.requirement,
                            self.agent,
                        )
                        self.console.log(task_dicts)
                        self.plan.tasks = []
                        for task_dict in task_dicts.get('tasks'):
                            task = match_plan(task_dict)
                            if task:
                                self.plan.tasks.append(task)

                    # Confirm the plan
                    confirm_plan = questionary.confirm("Are you sure to use this plan?").ask()
                    if confirm_plan:
                        self.update_project_state()
                    else:
                        self.console.log("Seems you are not satisfied with the plan. Aborting the chain.")
                        return

                task_num = len(self.plan.tasks)
                # check if all tasks are completed.
                if self.plan.current_task == task_num:
                    self.console.log(":tada: Looks like all tasks are completed.")
                    return

                # install the dependencies for this plan.
                setup_agent = SetupAgent(self.agent, self.plan)
                setup_agent.invoke()

                # code generation
                self.console.log("[bold red]Step 5: Code generation[bold red]")
                code_generation_agent = CodeGenerator(self.agent, self.plan, self.requirement)
                code_generation_agent.invoke(task_num)

                is_running = False
        except KeyboardInterrupt:
            self.console.log("MLE Plan Agent has been interrupted.")
            return
