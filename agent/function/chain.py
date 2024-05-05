import questionary
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.utils import *
from agent.types import Step, Task
from agent.const import CONFIG_TASK_HISTORY_FILE
from agent.prompt import pmpt_chain_init, pmpt_chain_code, pmpt_chain_filename, pmpt_chain_debug

config = Config()


class Chain:

    def __init__(self, step: Step, llm_agent):
        """
        Chain: the interactive chain of the current ML task.
        :param step: the step of the chain.
        :param llm_agent: the language model agent.
        """
        self.step = step
        self.agent = llm_agent
        self.chat_history = []
        self.console = Console()
        self.project_path = config.read()['project']['path']
        self.project_state = read_project_state(str(os.path.join(self.project_path, CONFIG_PROJECT_FILE)))
        self.project_home = config.read().get('project')['path']
        self.session = PromptSession(
            history=FileHistory(str(os.path.join(self.project_home, CONFIG_TASK_HISTORY_FILE)))
        )
        self.target_source = self.project_state.target_file
        self.user_requirement = self.project_state.user_requirement

    def update_project_state(self):
        """
        Update the project state.
        :return: None
        """
        update_project_state(self.project_home, self.project_state.dict(exclude_none=True))
        return self.project_state

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
        :param completion: the completion.
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
        prompt = pmpt_chain_filename(self.project_state.lang)
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
            self.target_source = os.path.join(self.project_state.path, target_name)

        self.console.print(f"The generated file name is: {self.target_source}")
        confirm = questionary.confirm("Do you want to use this name?").ask()
        if not confirm:
            new_name = questionary.text("Please provide a new file name:", default=self.target_source).ask()
            if new_name:
                self.target_source = os.path.join(self.project_state.path, new_name)

        # clear the chat history
        self.project_state.target_file = self.target_source
        self.chat_history = []

        return self.target_source

    def gen_task_content(self, task: Task, params=None):
        """
        Generate the content of the current task.
        :param task: the task to work on.
        :param params: the parameters of the previous task.

        :return: the content of the task.
        """
        language = self.project_state.lang
        target_source = self.project_state.target_file
        sys_prompt = pmpt_chain_init(language)
        if target_source:
            source_content = read_file_to_string(target_source)
            if source_content or self.project_state.task <= 1:
                sys_prompt = pmpt_chain_code(self.project_state.lang, source_content)
            else:
                self.console.log(
                    f"File {target_source} not found. "
                    f"Please make sure the current script exists or generate a new one by deleting the `target_file` in the project.yml \n"
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
        if task.debug:
            with self.console.status("Running the code script..."):
                run_log, exit_code = run_command(["python", self.target_source])
                console.log(run_log)

            if exit_code != 0:
                for attempt in range(task.debug):
                    self.console.log("Debugging the code script...")
                    self.chat_history.append({"role": 'system', "content": pmpt_chain_debug(language, code, run_log)})
                    code = self.handle_streaming()

        return code

    def start(self):
        """
        Execute the chain.
        :return: the result of the chain.
        """
        is_running = True
        while is_running:
            if self.project_state.user_requirement:
                self.console.print(f"User Requirement: {self.project_state.user_requirement}")
            else:
                self.user_requirement = questionary.text("What are the user requirements for the file name?").ask()
                self.project_state.user_requirement = self.user_requirement

            if self.target_source is None:
                if self.user_requirement:
                    self.target_source = self.gen_file_name(self.user_requirement)
                    self.console.print(f"The generated file name is: {self.target_source}")
                    self.update_project_state()

            # working on the task content.
            task_params = None
            task_num = len(self.step.tasks)
            for task in self.step.tasks:
                if self.project_state.task < task_num:
                    self.console.log(f"Working on task: {task.name} ({self.project_state.task + 1}/{task_num})")
                    if task.kind == 'code_generation':
                        result = self.gen_task_content(task, task_params)
                        if result is None:
                            self.console.log("[red]Task failed. Aborting the chain.")
                            return
                        task_params = None

                    if task.kind == 'multiple_choice':
                        task_params = self.ask_choice(task)

                    self.project_state.task += 1

                # update the project state after each task.
                self.update_project_state()

            is_running = False
            if self.project_state.task == task_num:
                self.console.print("Looks like all tasks are completed.")
                return
