import questionary
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.utils import *
from agent.types import Plan, Task
from agent.const import CONFIG_TASK_HISTORY_FILE
from agent.prompt import pmpt_chain_init, pmpt_chain_code, pmpt_chain_filename, pmpt_chain_debug

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
            self.console.print("You have not set up a project yet.")
            self.console.print("Please create a new project first using 'mle new' command then try again.")
            raise SystemExit

        self.project_home = config.read().get('project')['path']
        self.session = PromptSession(
            history=FileHistory(str(os.path.join(self.project_home, CONFIG_TASK_HISTORY_FILE)))
        )
        self.target_source = self.plan.target
        self.user_requirement = self.plan.requirement

    def update_project_state(self):
        """
        Update the project state.
        :return: None
        """
        update_project_plan(self.project_home, self.plan.dict(exclude_none=True))
        return self.plan

    def ask_choice(self, task: Task):
        """
        Ask a choice question.
        :param task: the task to work on.
        :return: the answer.
        """
        source_kind = questionary.select(task.description, [c.name for c in task.resources]).ask()
        if source_kind:
            for choice in task.resources:
                if choice.name == source_kind:
                    if choice.choices:
                        return questionary.select("Please select", choice.choices).ask()
                    return source_kind

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
                        Panel(Markdown(text), title="[bold magenta]MLE Assistant[/]", border_style="magenta"),
                        refresh=True
                    )

                stop_reason = token.choices[0].finish_reason
                if stop_reason == "stop":
                    code = extract_code(text)
                    if code:
                        with open(self.target_source, 'w') as file:
                            file.write(code)
                        self.console.print(f"Code generated to: {self.target_source}")
        return text

    def gen_file_name(self, user_requirement: str):
        """
        Generate a file name.
        :return: the file name.
        """
        prompt = pmpt_chain_filename(self.plan.lang)
        self.user_requirement = user_requirement
        self.chat_history.extend(
            [
                {"role": 'system', "content": prompt},
                {"role": 'user', "content": self.user_requirement}
            ]
        )

        with self.console.status("Generating file name..."):
            completion = self.agent.completions(self.chat_history, stream=False)
            target_name = extract_file_name(completion.choices[0].message.content)
            self.target_source = str(os.path.join(self.plan.project, target_name))

        # TODO: handle the keyboard interrupt.
        self.console.print(f"The generated file name is: {self.target_source}")
        confirm = questionary.confirm("Do you want to use this name?").ask()
        if not confirm:
            new_name = questionary.text("Please provide a new file name:", default=self.target_source).ask()
            if new_name:
                self.target_source = os.path.join(self.plan.path, new_name)

        # clear the chat history
        self.plan.target = self.target_source
        self.chat_history = []

        return self.target_source

    def gen_task_content(self, task: Task, params=None):
        """
        Generate the content of the current task.
        :param task: the task to work on.
        :param params: the parameters of the previous task.

        :return: the content of the task.
        """
        language = self.plan.lang
        target_source = self.plan.target
        sys_prompt = pmpt_chain_init(language)
        if target_source:
            source_content = read_file_to_string(target_source)
            if source_content or self.plan.current_task <= 1:
                sys_prompt = pmpt_chain_code(self.plan.lang, source_content)
            else:
                self.console.log(
                    f"File {target_source} not found. "
                    f"Please make sure the script exists or deleting the `target_file` in the project.yml \n"
                )
                return None

        task_prompt = f"""
        User Requirement: {self.user_requirement}
        Primary language: {language}
        Current task: {task.name}
        Task description: {task.description}
        """

        if params:
            task_prompt += f"""
            Resources: {params}
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
            command = f"python {self.target_source}"
            with self.console.status(f"Running the code script with command: {command}"):
                run_log, exit_code = run_command([command])

            if exit_code != 0:
                for attempt in range(task.debug):
                    self.console.log("Debugging the code script...")
                    self.chat_history.append(
                        {"role": 'user', "content": pmpt_chain_debug(language, self.user_requirement, code, run_log)})
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
                if self.plan.requirement:
                    self.console.print(f"User Requirement: {self.plan.requirement}")
                else:
                    self.user_requirement = questionary.text("Hi, what are your requirements?").ask()
                    self.plan.requirement = self.user_requirement

                if self.target_source is None:
                    if self.user_requirement:
                        self.target_source = self.gen_file_name(self.user_requirement)
                        if self.target_source is None:
                            return
                        self.console.print(f"The requirements are stored in: {self.target_source}")
                        self.update_project_state()

                # working on the task content.
                if self.plan.tasks is None:
                    self.console.log("No tasks found in the project plan. Planning the tasks for you...")

                    return

                task_params = None
                task_num = len(self.plan.tasks)
                for task in self.plan.tasks:
                    if self.plan.current_task < task_num:
                        self.console.log(f"Working on task: {task.name} ({self.plan.current_task + 1}/{task_num})")
                        if task.kind == 'code_generation':
                            result = self.gen_task_content(task, task_params)
                            if result is None:
                                self.console.log("[red]Task failed. Aborting the chain.")
                                return
                            task_params = None

                        if task.kind == 'multiple_choice':
                            task_params = self.ask_choice(task)

                        self.plan.current_task += 1

                    # update the project state after each task.
                    self.update_project_state()

                is_running = False
                if self.plan.current_task == task_num:
                    self.console.print("Looks like all tasks are completed.")
                    return
        except KeyboardInterrupt:
            self.console.print("The chain has been interrupted.")
            return