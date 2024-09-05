from rich.console import Console

from mle.function import *


class ClarifierAgent:

    def __init__(self, model, console=None):
        """
        ClarifierAgent: An agent to enhance the understanding of user needs through multiple rounds of
        Clarification Dialogue, which can improve the subsequent task generation effectiveness.

        Args:
            model: the model to use.
        """
        self.model = model
        self.chat_history = []

        self.console = console
        if not self.console:
            self.console = Console()

        self.sys_prompt = f"""
        You are an Machine learning Product Manager, you are going to collaborate with the user to plan the ML
        project. You need to ensure that the user's ML project has no ambiguities, for example, in the use of
        the dataset or the project requirements.

        You have the capability to interact with the user by invoking the following tools, thereby enhancing
        your understanding of the ML project. 

        1. Ask a multiple-choice question to the user by using function `ask_choices`.
        2. Ask a yes/no question to the user using function `ask_yes_no`.
        3. Ask a question to the user and get a response using function `ask_question`.
        
        If you can ensure there is no ambiguities in project understanding, output a short final summary.
        """

        self.functions = [
            schema_ask_choices,
            schema_ask_question,
            schema_ask_yes_no,
        ]

        self.chat_history.append({"role": "system", "content": self.sys_prompt})

    def interact(self, input: str, type: str):
        """
        Iteract with users to enhance the understanding of user needs
        Args:
            input (str): the project description.
            type (str): the type of the project description, 'dataset' or 'requirement'.
        """
        if type == "dataset":
            user_prompt = f"""
            The dataset description provided by the user for this project is: `{input}`
            If the dataset description is not a specific dataset or a valid file path, you can supply some publicly
            available datasets for the user to choose from. You can only ask the user within the calling functions no
            more than once. Then, you should output the final dataset name or path.
            """
        else:
            user_prompt = f"""
            The user's project requirement is: `{input}`
            If the requirements are not clear or have ambiguities, you should ask the user some questions, supply
            yes/no questions for the user to confirm, or provide some options inferred from the user's intentions
            to choose from. Output the final user's requirement once you have confirmed.
            """

        # with self.console.status("MLE Agent is understanding the requirements..."):
        self.chat_history.append({"role": "user", "content": user_prompt})
        text = self.model.query(
            self.chat_history,
            function_call="auto",
            functions=self.functions,
        )
        self.chat_history.append({"role": "assistant", "content": text})
        return text
