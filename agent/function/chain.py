import questionary
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.utils import *
from agent.types import Plan, Task
from agent.integration import read_csv_file
from agent.hub.utils import match_plan
from agent.types.const import CONFIG_TASK_HISTORY_FILE
from agent.utils.prompt import pmpt_chain_init, pmpt_chain_code, pmpt_chain_filename, pmpt_chain_debug

from .generator import plan_generator, dependency_generator, req_based_generator

config = Config()


class Chain:
    def __init__(self, plan: Plan, llm_agent):
        """
        Chain: the interactive chain of the current ML task.
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
        self.project_name = self.plan.project_name
        self.dataset = self.plan.dataset

    def update_project_state(self):
        """
        Update the project state.
        :return: None
        """
        update_project_plan(self.project_home, self.plan.dict(exclude_none=True))
        return self.plan

    def handle_streaming(self):
        """
        Handle the streaming completion.
        :return: the result.
        """
        text = ""
        with Live(console=self.console) as live:
            for token in self.agent.completions(self.chat_history, stream=True):
                content = token.choices[0].delta.content
                if content:
                    text = text + content
                    live.update(
                        Panel(Markdown(text), title="[bold magenta]MLE-Agent[/]", border_style="magenta"),
                        refresh=True
                    )

                stop_reason = token.choices[0].finish_reason
                if stop_reason == "stop":
                    code = extract_code(text)
                    if code:
                        with open(self.entry_file, 'w') as file:
                            file.write(code)
                        self.console.log(f"Code generated to: {self.entry_file}")
        return text

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
            completion = self.agent.completions(self.chat_history, stream=False)
            target_name = extract_file_name(completion.choices[0].message.content)
            self.entry_file = str(os.path.join(self.plan.project, target_name))

        # TODO: handle the keyboard interrupt.
        self.console.log(f"The entry file is: {self.entry_file}")
        confirm = questionary.confirm("Do you want to use the file?").ask()

        if not confirm:
            new_name = questionary.text("Please provide a new file name:", default=self.entry_file).ask()
            if new_name:
                self.entry_file = os.path.join(self.plan.path, new_name)

        # clear the chat history
        self.plan.entry_file = self.entry_file
        self.chat_history = []

        return self.entry_file

    def gen_task_content(self, task: Task):
        """
        Generate the content of the current task.
        :param task: the task to work on.

        :return: the content of the task.
        """
        language = self.plan.lang
        entry_file = self.plan.entry_file
        sys_prompt = pmpt_chain_init(language)
        if entry_file:
            source_content = read_file_to_string(entry_file)
            if source_content or self.plan.current_task <= 1:
                sys_prompt = pmpt_chain_code(self.plan.lang, source_content)
            else:
                self.console.log(
                    f"File {entry_file} not found. "
                    f"Please make sure the script exists or deleting the `target_file` in the project.yml \n"
                )
                return None

        task_prompt = f"""
        User Requirement: {self.requirement}
        Primary language: {language}
        Current task: {task.name}
        Task description: {task.description}
        """

        # handle the data collection task.
        if task.name == "Data Collection":
            if self.plan.data_kind == 'csv_data':
                task_prompt += f"""
                Data source: {self.plan.dataset}
                Dataset examples: {read_csv_file(self.plan.dataset, column_only=True)}
                """

        self.chat_history.extend(
            [
                {"role": 'system', "content": sys_prompt},
                {"role": 'user', "content": task_prompt}
            ]
        )

        code = self.handle_streaming()
        # TODO: allow generating the command to run the code script.
        # TODO: allow handling the issues that are not comes from the code script.
        # TODO: allow handling the program timeout.
        if task.debug:
            debug_success = False
            command = f"python {self.entry_file}"
            with self.console.status(f"Running the code script with command: {command}"):
                run_log, exit_code = run_command([command])

            if exit_code != 0:
                for attempt in range(task.debug):
                    self.console.log("Debugging the code script...")
                    self.chat_history.append(
                        {"role": 'user', "content": pmpt_chain_debug(language, self.requirement, code, run_log)})
                    code = self.handle_streaming()
                    with self.console.status(f"Running the code script..."):
                        run_log, exit_code = run_command([command])

                    if exit_code == 0:
                        debug_success = True
                        self.console.log("Debugging successful, the code script has been saved.")
                        break

                if not debug_success:
                    self.console.log(f"Debugging failed after {task.debug} attempts.")
                    return None

        return code

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
                if self.plan.data_kind is None:
                    self.plan.data_kind = req_based_generator(self.requirement, pmpt_dataset_detect(), self.agent)
                    if self.plan.data_kind == 'no_data_information_provided':
                        self.plan.dataset = req_based_generator(self.requirement, pmpt_dataset_select(), self.agent)
                    elif self.plan.data_kind == 'csv_data':
                        self.plan.dataset = questionary.text("Please provide the CSV data path:").ask()

                self.console.log(f"[cyan]Data source:[/cyan] {self.plan.dataset}")
                if self.plan.dataset is None or os.path.exists(self.plan.dataset) is False:
                    raise SystemExit("Wrong dataset information. Aborted.")
                else:
                    csv_data_sample = read_csv_file(self.plan.dataset)
                    self.console.log(f"[cyan]Dataset examples:[/cyan] {csv_data_sample}")
                    self.requirement += f"\n\nDataset Sample: {csv_data_sample}"

                self.console.log("[bold red]Step 3: Task & Model selection[bold red]")
                if self.plan.tasks is None:
                    self.console.log(
                        f"The project [cyan]{self.project_name}[/cyan] has no existing plans. Start planning...")

                    ml_task_name = req_based_generator(self.requirement, pmpt_task_select(), self.agent)
                    self.console.log(f"[cyan]Task detected:[/cyan] {ml_task_name}")
                    self.requirement += f"\n\nML Task: {ml_task_name}"

                    # TODO: search the best model from kaggle, huggingface, etc
                    ml_model_arch = req_based_generator(self.requirement, pmpt_model_select(), self.agent)
                    self.console.log(f"[cyan]Model architecture selected:[/cyan] {ml_model_arch}")

                    # Step 4: Generate the plan and tasks
                    self.console.log("[bold red]Step 4: Plan generation[bold red]")
                    with self.console.status("Planning the tasks for you..."):
                        task_dicts = plan_generator(
                            self.requirement,
                            self.agent,
                            ml_model_arch,
                            self.plan.dataset,
                            ml_task_name
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
                with self.console.status("Installing the dependencies for the plan..."):
                    install_commands = dependency_generator(self.plan, self.agent).get('commands')
                    self.console.log(f"[cyan]Commands are going to execute:[/cyan] {install_commands}")

                # confirm the installation.
                confirm_install = questionary.confirm("Are you sure to install the dependencies?").ask()
                if confirm_install:
                    run_command(install_commands)
                else:
                    self.console.log("Skipped the dependencies installation.")

                for task in self.plan.tasks:
                    if self.plan.current_task < task_num:
                        self.console.log(f"Working on task: {task.name} ({self.plan.current_task + 1}/{task_num})")
                        # TODO: add supports for other kind of tasks.
                        if task.kind == 'code_generation':
                            result = self.gen_task_content(task)
                            if result is None:
                                self.console.log("[red]Task failed. Aborting the chain.")
                                return

                        self.plan.current_task += 1
                    self.update_project_state()

                is_running = False
        except KeyboardInterrupt:
            self.console.log("The chain has been interrupted.")
            return
