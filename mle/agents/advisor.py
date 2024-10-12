import sys
import json
from rich.console import Console

from mle.function import *
from mle.utils import get_config, print_in_box, clean_json_string


def process_report(requirement: str, suggestions: dict):
    return textwrap.dedent(f"""
{requirement}

[green]Dataset Summary:[/green] {suggestions.get('data_summary')}

[green]Suggestion Summary:[/green] {suggestions.get('suggestion')}

[green]Task:[/green] {suggestions.get('task')}
[green]Model:[/green] {suggestions.get('model_or_algorithm')}
[green]Training Strategy:[/green] {suggestions.get('training_method')}
[green]Evaluation Metric:[/green] {suggestions.get('evaluation_metric')}
[green]Training Device:[/green] {suggestions.get('device')}

[green]Serving Strategy:[/green] {suggestions.get('serving_method')}

[green]Reference:[/green] {suggestions.get('reference')}
[green]Dependency:[/green] {suggestions.get('frameworks')}
""").strip()


class AdviseAgent:

    def __init__(self, model, console=None, mode='normal'):
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

        - Read and understand the dataset information and user's requirements, the requirements may include the task,
         the model (or method), and the evaluation metrics, etc. You should always follow the user's requirements.
        - You should briefly analyze the user's dataset, and give a summary of the dataset, the dataset input can be
         a public dataset name or a path to a local CSV file. You can use the function `preview_csv_data` to preview
         the CSV files or not if the dataset is a public dataset.
        - And then you should always use the function `search_arxiv` or `search_papers_with_code` to search the
         state-of-the-art machine learning tasks/models/algorithms that can be used to solve the user's requirements,
          and stay up-to-date with the latest.
        - If the user does not provide the details (task/model/algorithm/dataset/metric), you should always suggest.
        - You should provide the paper reference links of the task/model/algorithm/metric you suggest. You use the
         search results from the function `search_arxiv` or `search_papers_with_code` by generated search keywords.
        - The suggestion should be as detailed as possible, include the SOTA methods for data processing, feature
         extraction, model selection, training/sering methods and evaluation metrics. And the reasons why you suggest.
        - You should help user to decide which framework/tools to use for the project, such as PyTorch, TensorFlow,
         MLFlow, W&B, etc.
        """
        self.search_prompt = """
        - You should also use function `web_search` to search for articles, papers, or tutorials related to the
         task/model/algorithm/metric to help you decide which one to use.
        """
        self.json_mode_prompt = """

        JSON Output Format:
        
        {
            "task":"xxxxx",
            "model_or_algorithm":"xxxx",
            "frameworks": ["xxxx", "xxxx"],
            "reference": ["xxxx", "xxxx"],
            "evaluation_metric": ["xxx", "xxx"],
            "training_method": "xxxx",
            "serving_method": "Serving is not required",
            "device": "xxxx",
            "data_summary": "The data provided is a..., it contains...",
            "suggestion": "Based on the user requirement, we suggest you to..."
        }
        
        """

        # precise means the user has provided specific requirements with metrics, models, etc.
        if mode == 'precise':
            self.sys_prompt = f"""
            You are an Machine learning expert tasked with advising on the best ML task/model/algorithm to use.
            
            Your capabilities include:
            
            - Based on the requirements, give suggestions on how to maximize the performance of the task metrics.
            - Use the function `search_arxiv` or `search_papers_with_code` to search the state-of-the-art machine learning
               tasks/models/algorithms that can be used to solve the user's requirements, and stay up-to-date with the latest.
            - You should help user to decide which framework/tools to use to implement the project, such as PyTorch, TensorFlow, etc.
            - You should apply some tricks to improve the performance of the model, detail the implementation steps of each trick.
                       
            """

            self.json_mode_prompt = """

            JSON Output Format:

            {
                "task":"xxxxx",
                "model_or_algorithm":"xxxx",
                "frameworks": ["xxxx", "xxxx"],
                "training_method": "xxxx",
                "suggestion": "Based on the user requirement, we suggest you to... and why...",
                "tricks": ["xxx", ...]
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

    def suggest(self, requirement, return_raw=False):
        """
        Handle the query from the model query response.
        Args:
            requirement: the user requirement.
            return_raw: whether to process the report.
        """
        with self.console.status("MLE Advisor is thinking the best strategy to help you..."):
            self.chat_history.append({"role": "user", "content": requirement})
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})
            try:
                suggestions = json.loads(text)
            except json.JSONDecodeError as e:
                suggestions = clean_json_string(text)

        if return_raw:
            return suggestions

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
                "Suggestions to improve the report? (ENTER to move to the next stage, \"exit\" to exit the project)"
            ).ask()

            if not question:
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

    def clarify_dataset(self, dataset: str):
        """
        Clarify the dataset blurity by suggest some datasets.
        Args:
            dataset: the user's input dataset name.
        """
        system_prompt = """
        You are an Machine learning Product Manager, you are going to collaborate with the user to plan
        the ML project, in the use of the dataset.
        """
        chat_history = [{"role": "system", "content": system_prompt}]

        # verify whether the user's dataset is unclear or blur
        user_prompt = f"""
        The dataset provided by the user is: `{dataset}`

        Your task is to determine if the dataset refers to:
        1. A specific dataset name, or
        2. A file path.

        Response format: Yes / No
        - Yes: if the dataset is clearly identifiable as either a specific dataset name or a file path.
        - No: if the dataset cannot be clearly identified as either a specific dataset name or a file path.
        """
        with self.console.status("MLE Advisor is verifing dataset..."):
            chat_history.append({"role": "user", "content": user_prompt})
            text = self.model.query(chat_history)
            chat_history.append({"role": "assistant", "content": text})
            if "yes" in text.lower():
                return dataset

        # recommend some datasets based on the users' description
        user_prompt = f"""
        Since the user has not provided a specific dataset, suggest up to five publicly available datasets
        that best match the user's description ({dataset}). Ensure your recommendations are concise and
        include a clear explanation (within 100 words) for why each dataset is appropriate.

        Json output format:
        {{
            "datasets": ["xxx", "xxx", "xxx"],
            "reason": "Based on the user's dataset description..."
        }}
        """
        with self.console.status("MLE Advisor is suggesting datasets..."):
            chat_history.append({"role": "user", "content": user_prompt})
            text = self.model.query(
                chat_history,
                response_format={"type": "json_object"}
            )
            chat_history.append({"role": "assistant", "content": text})
            suggestions = json.loads(text)

        print_in_box("Which datasets would you like?", title="MLE Advisor", color="green")
        return questionary.select("Type your answer here:", choices=suggestions['datasets']).ask()
