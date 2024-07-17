import sys
import json
from rich.console import Console

from mle.function import *
from mle.utils import get_config, print_in_box


def process_report(requirement: str, suggestions: dict):
    return textwrap.dedent(f"""
{requirement}
Dataset summary: {suggestions.get('data_summary')}
The ML task: {suggestions.get('task')}
The model or algorithm: {suggestions.get('model_or_algorithm')},
The training method: {suggestions.get('training_method')},
The serving method: {suggestions.get('serving_method')},
The reference: {suggestions.get('reference')},
The evaluation metric: {suggestions.get('evaluation_metric')},
The device: {suggestions.get('device')},
The suggestion: {suggestions.get('suggestion')}
""").strip()


class AdviseAgent:

    def __init__(self, model, console=None):
        """
        AdviseAgent: the agent to suggest which machine learning task/model/dataset to use based on the user's
        requirements. The return of the agent is an instruction to the user to modify the code based on the logs and
        web search.

        Args:
            model: the model to use.
            console: the console to use.
        """
        config_data = get_config()
        self.report = None
        self.model = model
        self.chat_history = []
        self.console = console
        if not self.console:
            self.console = Console()
        self.sys_prompt = """
        You are an Machine learning expert tasked with advising on the best ML task/model/algorithm to use.
        
        Your capabilities include:

        1. Read and understand the dataset information and user's requirements, the requirements may include the task,
         the model (or method), and the evaluation metrics, etc. You should always follow the user's requirements.
        2. You should briefly analyze the user's dataset, and give a summary of the dataset, the dataset input can be
         a public dataset name or a path to a local CSV file. You can use the function `preview_csv_data` to preview
         the CSV file.
        3. And then you should always use the function `search_arxiv` or `search_papers_with_code` to search the
         state-of-the-art machine learning tasks/models/algorithms that can be used to solve the user's requirements,
          and stay up-to-date with the latest.
        4. If the user does not provide the details (task/model/algorithm/dataset/metric), you should always suggest.
        5. You should provide the paper reference of the task/model/algorithm/metric you suggest. You use the search
         results from the function `search_arxiv` or `search_papers_with_code` by generated search keywords.
        6. The suggestion should be as detailed as possible, include the SOTA methods for data processing, feature
         extraction, model selection, training/sering methods and evaluation metrics. And the reasons why you suggest.
        """
        self.search_prompt = """
        7. You should also use function `web_search` to search for articles, papers, or tutorials related to the
         task/model/algorithm/metric to help you decide which one to use.
        """
        self.json_mode_prompt = """

        JSON Output Format:
        
        {
            "task":"xxxxx",
            "model_or_algorithm":"xxxx",
            "reference": ["xxxx", "xxxx"],
            "evaluation_metric": ["xxx", "xxx"],
            "training_method": "xxxx",
            "serving_method": "Serving is not required",
            "device": "xxxx",
            "data_summary": "The data provided is a..., it contains...",
            "suggestion": "Based on the user requirement, we suggest you to..."
        }
        
        """
        self.functions = [
            schema_web_search,
            schema_search_arxiv,
            schema_search_papers_with_code,
            schema_preview_csv_data
        ]
        if config_data.get('search_key'):
            self.functions.append(schema_web_search)
            self.sys_prompt += self.search_prompt

        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def suggest(self, requirement):
        """
        Handle the query from the model query response.
        Args:
            requirement: the user requirement.
        """
        with self.console.status("Advisor is thinking the suggestion for the requirements..."):
            self.chat_history.append({"role": "user", "content": requirement})
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})
            suggestions = json.loads(text)

        return process_report(requirement, suggestions)

    def interact(self, requirement):
        """
        Interact with the user to ask and suggest.
        Args:
            requirement: the initial user requirements.
        """
        self.report = self.suggest(requirement)
        print_in_box(self.report, title="MLE Advisor", color="green")
        while True:
            question = questionary.text(
                "Suggestions to improve the report? (empty answer or \"no\" to move to the next stage)").ask()

            if not question or question.lower() in ["no"]:
                break

            if question.lower() in ["exit"]:
                sys.exit(0)

            with self.console.status("Advisor is thinking the suggestion for the requirements..."):
                self.chat_history.append({"role": "user", "content": question})
                suggestions = self.model.query(
                    self.chat_history,
                    function_call='auto',
                    functions=self.functions,
                    response_format={"type": "json_object"}
                )

                self.report = process_report(requirement, json.loads(suggestions))
                print_in_box(self.report, title="MLE Advisor", color="green")

        return self.report
