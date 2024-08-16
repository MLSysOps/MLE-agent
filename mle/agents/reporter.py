import sys
import json
from rich.console import Console

from mle.function import *
from mle.utils import get_config, print_in_box, dict_to_markdown


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


class ReportAgent:

    def __init__(self, model, console=None):
        """
        ReportAgent: upgrade from the AdvisorAgent, the agent to provide suggestions based on the user requirements.
        The agent will analyze the user requirements and then provide the suggestions on the best machine learning task,
        model, dataset, and evaluation metrics to use. And reads the current workspace to provide the suggestions and
         summary.

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
        5. You should provide the paper reference links of the task/model/algorithm/metric you suggest. You use the
         search results from the function `search_arxiv` or `search_papers_with_code` by generated search keywords.
        6. The suggestion should be as detailed as possible, include the SOTA methods for data processing, feature
         extraction, model selection, training/sering methods and evaluation metrics. And the reasons why you suggest.
        7. You should help user to decide which framework/tools to use for the project, such as PyTorch, TensorFlow,
         MLFlow, W&B, etc.
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

    def infer(self):
        """
        Handle the query from the model query response.
        Args: None
        """
        with self.console.status("MLE Advisor is thinking the best strategy to help you..."):
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})
            suggestions = json.loads(text)

        return suggestions

    def interact(self, requirement):
        """
        Interact with the user to ask and suggest.
        Args:
            requirement: the initial user requirements.
        """
        self.chat_history.append({"role": "user", "content": requirement})
        while True:
            self.report = self.infer()
            self.report.update({"user_requirement": requirement})
            print_in_box(process_report(requirement, self.report), title="MLE Advisor", color="green")
            question = questionary.text(
                "Suggestions to improve the report? (ENTER or \"exit\" to exit the project)"
            ).ask()

            if not question:
                savefile = questionary.confirm(
                    "Do you want to save the report to a markdown file under the current workspace?"
                ).ask()

                if savefile:
                    dict_to_markdown(self.report, './advisor_report.md')
                    print_in_box(
                        "The report has been saved to 'advisor_report.md'.",
                        title="MLE Advisor",
                        color="green"
                    )
                    break

            if question.lower() in ["exit"]:
                sys.exit(0)

            self.chat_history.append({"role": "user", "content": question})
        return self.report
