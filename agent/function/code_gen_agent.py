from .base import BaseAgent
from agent.types import Task
from agent.utils import read_file_to_string, update_project_state


class CodeAgent(BaseAgent):

    def system_pmpt_code_gen_new(self) -> str:
        return f"""
        You are a Machine Learning engineer working on an ML project using {self.project.lang} as the primary language.
        The user requires a new code script for the current task. Please read users requirement and task description
        very carefully and generate a new code script that meets them step by step.
        Please make sure only output code with appropriate comments and documentation.

        The output format should be:

        Code: {{code}}
        """

    def system_pmpt_code_gen_existing(self, code: str) -> str:
        return f"""
        You are a Machine Learning engineer working on an ML project using {self.project.lang} as the primary language.
        The user requires modifications to the existing code to meet the task requirements and finish the project.
        Please use the following information to modify or add new changes to the code to finish the task and project.
        Please think this as a requirement, task and code review and make necessary changes to the code.
        Please make sure only output code with appropriate comments and documentation.
        Please think step by step.


        Existing Code: {code}

        The output format should be:

        Code: {{code}}
        """

    def task_prompt(self, task: Task, requirement) -> str:

        # TODO: need to find a better way to read user's requirement
        # TODO: 3 requirements are ugly

        return f"""
        User Requirement: {requirement}
        Primary Language: {self.project.lang}
        Current Task: {task.name}
        Task Description: {task.description}
        """

    def gen_code(self, task: Task, requirement):
        """
        Generate the content of the current task.
        :param task: the task to work on
        :param requirement: the user's requirement

        :return: the content of the task.
        """
        entry_file = self.project.entry_file
        sys_prompt = self.system_pmpt_code_gen_new()
        if entry_file:
            existing_code = read_file_to_string(entry_file)
            if existing_code or self.project.plan.current_task <= 1:
                sys_prompt = self.system_pmpt_code_gen_existing(existing_code)
            else:
                self.console.log(
                    f"File {entry_file} not found. "
                    f"Please make sure the script exists or deleting the {entry_file} in the project.yml \n"
                )
                return None

        self.chat_history.extend(
            [
                {"role": 'system', "content": sys_prompt},
                {"role": 'user', "content": self.task_prompt(task, requirement)}
            ]
        )

        code = self.handle_streaming()
        return code

    def invoke(self, task_num, requirement):
        for task in self.project.plan.tasks:
            if self.project.plan.current_task < task_num:
                self.console.log(f"Working on task: {task.name} ({self.project.plan.current_task + 1}/{task_num})")
                # TODO: add supports for other kind of tasks.
                if task.kind == 'code_generation':
                    result = self.gen_code(task, requirement)
                    if result is None:
                        self.console.log("[red]Task failed. Aborting the chain.")
                        return

                self.project.plan.current_task += 1
            update_project_state(self.project)
