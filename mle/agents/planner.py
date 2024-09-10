import sys
import json
import questionary
from rich.console import Console

from mle.utils import print_in_box, clean_json_string


def process_plan(plan_dict: dict):
    plan_str = ""
    for task in plan_dict.get('tasks'):
        plan_str += f"[green][Task]:[/green] {task.get('task')}\n[green][Description]:[/green] {task.get('description')}\n\n"

    return plan_str


class PlanAgent:

    def __init__(self, model, console=None):
        """
        PlanAgent: the agent to plan the machine learning project. By receiving the user's requirements, the agent will
        first analyze the requirements and ask the user to provide more details if necessary. Then the agent will
        generate the project plan based on the requirements and the user's input.

        The project plan will be sent to the advisor agent to provide suggestions on the best machine learning task,
        model, dataset, and evaluation metrics to use.

        Args:
            model: the model to use.
        """
        self.console = console
        if not self.console:
            self.console = Console()

        self.plan_dict = None
        self.model = model
        self.chat_history = []
        self.sys_prompt = """
        You are an Machine learning Product Manager, you are going to collaborate with the user to plan the ML
         project. A generated plan includes the coding tasks for the developer to complete the project.

        Your capabilities include:

        1. Understand the user's dataset and the user's requirements, the requirements may include the intention of the
         project, the model or algorithm to use, the dataset, the evaluation metrics, and the expected results. The
         generated task should always meet the user's requirements.
        2. The generated plan should include several coding tasks, and the task should include specific instructions for
         the developer. For example: "Create a directory named 'dataset' under the project root, and write a Python
         script called 'data_loader.py' to download the dataset ImageNet from the official website."
        3. The coding task should be clear and easy to understand, but with essential information to complete the task.
         For example, if the dataset is a user's local CSV file, you should provide the absolute path to the file in the
          task, otherwise, the developer may not be able to complete the task.
        4. Please only provide the coding tasks, do not provide the code snippets, the developer will complete the task.
        5. Do not generate task like "setup environment", "install dependencies", "run the code", etc. The developer
         only focus on the coding tasks.
    
        """
        self.json_mode_prompt = """

        Example JSON output:

        {
              "tasks": [
                    {
                        "task": "download dataset",
                        "description": "Create a directory named 'dataset' under the project root, and write a Python
                          script called 'data_loader.py' to download the dataset ImageNet from the official website."
                    },
                    {
                        "task": "process ImageNet",
                        "description": "Write a Python script called `process_data.py` to process the dataset by
                         resizing the images to 224x224 pixels and save the data to the 'processed_data' directory."
                    },
                    {
                        "task": "train model",
                        "description": "Write a Python script called `train_model.py` to train an image classification
                          model on the processed data and save the trained model to the 'model' directory."
                    }
              ]
        }
        """
        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def plan(self, user_prompt):
        """
        Handle the query from the model query response.
        Args:
            user_prompt: the user prompt.
        """
        with self.console.status("MLE Planner is planning the coding tasks..."):
            self.chat_history.append({"role": "user", "content": user_prompt})
            text = self.model.query(
                self.chat_history,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            return clean_json_string(text)

    def interact(self, user_prompt):
        """
        Handle the query from the model query response.
        Args:
            user_prompt: the user prompt.
        """
        self.plan_dict = self.plan(user_prompt)
        print_in_box(process_plan(self.plan_dict), self.console, title="MLE Planner", color="purple")

        while True:
            suggestion = questionary.text(
                "Suggestions to improve the plan? (ENTER to move to the next stage, \"exit\" to exit the project)"
            ).ask()

            if not suggestion or suggestion.lower() == "no":
                break

            if suggestion.lower() == "exit":
                sys.exit(0)

            self.plan_dict = self.plan(suggestion)
            print_in_box(process_plan(self.plan_dict), self.console, title="MLE Planner", color="purple")

        return self.plan_dict