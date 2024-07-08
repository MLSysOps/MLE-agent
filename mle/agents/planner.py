from mle.function import *


class PlanAgent:

    def __init__(self, model):
        """
        PlanAgent: the agent to plan the machine learning project. By receiving the user's requirements, the agent will
        first analyze the requirements and ask the user to provide more details if necessary. Then the agent will
        generate the project plan based on the requirements and the user's input.

        The project plan will be sent to the advisor agent to provide suggestions on the best machine learning task,
        model, dataset, and evaluation metrics to use.

        Args:
            model: the model to use.
        """
        self.model = model
        self.chat_history = []
        self.sys_prompt = """
        You are an Machine learning Product Manager, you are going to collaborate with the user to plan the ML
         project. Your goal is to generate the project plan based on the user's requirements and the user's input.

        Your capabilities include:

        1. Understand the user's requirements, the requirements may include the task, the dataset, the model, and the
            evaluation metrics, or it can be a general requirement. You should always follow the user's requirements.
        2. Help the user enhance the requirements by asking questions or providing choices for some details in the
            requirements. For example, the user asks for a model, you can ask the user to provide more details about the
            task that the model will be used for; If the user ask you to write a script to process an existing dataset,
            you should ask the user to provide the dataset format, and the expected output, etc.
        3. The generated plan should include several coding tasks, and the task should include specific instructions for
            the developer. For example: "Create a directory named 'dataset' under the project root, and write a Python
            script called 'data_loader.py' to download the dataset ImageNet from the official website."
        4. The questions you ask should be clear and concise, and the choices you provide should be relevant to the
            user's requirements. The user has the right to skip the questions.
        
        The functions you can use:
        
        1. `ask_question` to ask the user questions.
        2. `ask_choices` to provide the user with choices.
        3. `ask_yes_no` to ask the user to provide a yes/no answer.
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
                        "description": "Write a Python script called `process_data.py` to process the dataset by resizing
                          the images to 224x224 pixels and save the processed data to the 'processed_data' directory."
                    },
                    {
                        "task": "train model",
                        "description": "Write a Python script called `train_model.py` to train an image classification
                          model on the processed data and save the trained model to the 'model' directory."
                    },
                    {
                        "task": "evaluate model",
                        "description": "Added a Python function in the `train_model.py` script to evaluate the trained
                          model using the test dataset and print the evaluation metrics."
                    }
              ]
        }
        """
        self.functions = [
            schema_ask_question,
            schema_ask_yes_no,
            schema_ask_choices
        ]

        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def plan(self, user_prompt):
        """
        Handle the query from the model query response.
        Args:
            user_prompt: the user prompt.
        """
        self.chat_history.append({"role": "user", "content": user_prompt})
        text = self.model.query(
            self.chat_history,
            function_call='auto',
            functions=self.functions,
            response_format={"type": "json_object"}
        )

        self.chat_history.append({"role": "assistant", "content": text})
        return text
