from mle.function import *
from mle.utils import get_config


class AdviseAgent:

    def __init__(self, model):
        """
        AdviseAgent: the agent to suggest which machine learning task/model/dataset to use based on the user's
        requirements. The return of the agent is an instruction to the user to modify the code based on the logs and
        web search.

        Args:
            model: the model to use.
        """
        config_data = get_config()
        self.model = model
        self.chat_history = []
        self.sys_prompt = """
        You are an Machine learning expert tasked with advising on the best machine learning task/model/dataset to use.
        
        Your capabilities include:

        1. Read and understand the user's requirements, the requirements may include the task, the dataset, the model,
            and the evaluation metrics. You should always follow the user's requirements.
        2. If the user does not provide the details (task/model/dataset/evaluation metrics), you should provide them.
        3. Use the function `search_arxiv` to search the state-of-the-art machine learning
         tasks/models/datasets that can be used to solve the user's requirements, and stay up-to-date with the latest.
        4. You should provide the paper reference of the task/model/dataset/metrics you suggest if any. You may need
        to call the `search_arxiv` function to find the reference from the arxiv.
        """
        self.search_prompt = """
        5. You can also use function `web_search` to search for articles, papers, or tutorials related to the
         task/model/dataset to help you decide which one to use.
        """
        self.json_mode_prompt = """

        Example JSON output:
        
        {
              "task":"image-classification",
              "model":"Random Forest",
              "dataset":"iris",
              "reference": ["10.1109/ICDM50108.2020.00131"],
              "evaluation_metric": ["accuracy", "precision", "recall", "f1"]
        }
        
        {
            "task":"text-classification",
            "model":"BERT-base",
            "dataset":"IMDB Reviews",
            "reference": ["https://arxiv.org/abs/1810.04805"],
            "evaluation_metric": ["accuracy", "f1"]
        }
        
        """
        self.functions = [
            search_arxiv
        ]

        if config_data.get('search_key'):
            self.functions.append(schema_web_search)
            self.sys_prompt += self.search_prompt

        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def suggest(self, user_prompt):
        """
        Handle the query from the model query response.
        Args:
            user_prompt: the user prompt.
        """
        self.chat_history.append({"role": "user", "content": "Advisor: " + user_prompt})
        text = self.model.query(
            self.chat_history,
            function_call='auto',
            functions=self.functions,
            response_format={"type": "json_object"}
        )

        self.chat_history.append({"role": "assistant", "content": text})
        return text
