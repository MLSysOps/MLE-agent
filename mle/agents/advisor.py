import json

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
        self.ask_history = []
        self.sys_prompt = """
        You are an Machine learning expert tasked with advising on the best machine learning task/model/dataset to use.
        
        Your capabilities include:

        1. Read and understand the user's requirements, the requirements may include the task, the dataset, the model,
            and the evaluation metrics. You should always follow the user's requirements.
        2. And then you should use the function `search_arxiv` to search the state-of-the-art machine learning
         tasks/models/datasets that can be used to solve the user's requirements, and stay up-to-date with the latest.
        3. If the user does not provide the details (task/model/dataset/metric), you should provide them.
        4. You should provide the paper reference of the task/model/dataset/metric you suggest. You use the search
         results from the function `search_arxiv` by generating keywords from the requirements and Q/A.
        """
        self.ask_prompt = """
        You are an Machine learning expert, now you are talking to the user to help them write better ML project
         requirements.
         
        Your capabilities include:
        1. Read the user requirements and trying to understand the user's intent.
        2. Decide if the requirement is clear enough or not. If not clear, you should ask the user to provide more
         details.
        3. It is ok for the users to provide unclear answers, but you job is to help user understand the goal that
         the user wants to achieve, and with as more as details.
        4. You question should be clear and simple, do not ask too many questions at once, you should ask them one
         by one. For example: "What kind of data you are using locally?", "What kind of ML task you want to do?",
         "What evaluation metrics you want to use?".
         
         You should KEEP asking until you think the requirement can clearly show the user's intent. But ask
          the minimum number of question as you can.
            
         Example responses in JSON format:
         
         {"status": "unclear", "question": "What is your dataset looks like?"}
         
         {"status": "completed", "question": ""}
                
        """
        self.search_prompt = """
        5. You should also use function `web_search` to search for articles, papers, or tutorials related to the
         task/model/dataset/metric to help you decide which one to use.
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
        self.functions = [schema_search_arxiv]
        if config_data.get('search_key'):
            self.functions.append(schema_web_search)
            self.sys_prompt += self.search_prompt

        self.sys_prompt += self.json_mode_prompt
        self.ask_history.append({"role": 'system', "content": self.ask_prompt})
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def ask(self, requirement):
        """
        Help the user write better requirements.
        Args:
            requirement: the initial user requirements.
        """

        self.ask_history.append({"role": "user", "content": requirement})
        text = self.model.query(
            self.ask_history,
            response_format={"type": "json_object"}
        )

        self.ask_history.append({"role": "assistant", "content": text})
        resp = json.loads(text)

        if resp.get("status") == "unclear":
            question = resp.get("question")
            answer = questionary.text(question).ask()
            if answer:
                self.ask_history.append({"role": "user", "content": answer})
                requirement += f"\nQuestion: {question}\nAnswer: {answer}"
                return self.ask(requirement)
        else:
            return requirement

    def suggest(self, requirement):
        """
        Handle the query from the model query response.
        Args:
            requirement: the user requirement.
        """
        self.chat_history.append({"role": "user", "content": requirement})
        text = self.model.query(
            self.chat_history,
            function_call='auto',
            functions=self.functions,
            response_format={"type": "json_object"}
        )

        self.chat_history.append({"role": "assistant", "content": text})
        return json.loads(text)
