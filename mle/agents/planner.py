import json


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
        2. The generated plan should include several coding tasks, and the task should include specific instructions for
            the developer. For example: "Create a directory named 'dataset' under the project root, and write a Python
            script called 'data_loader.py' to download the dataset ImageNet from the official website."
    
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
        self.chat_history.append({"role": "user", "content": user_prompt})
        text = self.model.query(
            self.chat_history,
            response_format={"type": "json_object"}
        )

        self.chat_history.append({"role": "assistant", "content": text})
        return json.loads(text)
