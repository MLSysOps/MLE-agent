import sys
import json
from rich.console import Console

from mle.function import *
from mle.utils import get_config, print_in_box


def process_report(requirement: str, suggestions: dict):
    return textwrap.dedent(f"""
                {requirement}
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
        self.ask_history = []
        self.console = console
        if not self.console:
            self.console = Console()
        self.sys_prompt = """
        You are an Machine learning expert tasked with advising on the best ML task/model/algorithm to use.
        
        Your capabilities include:

        1. Read and understand the dataset information and user's requirements, the requirements may include the task,
         the model, and the evaluation metrics, etc. You should always follow the user's requirements.
        2. And then you should use the function `search_arxiv` or `search_papers_with_code` to search the
         state-of-the-art machine learning tasks/models that can be used to solve the user's requirements, and stay
         up-to-date with the latest.
        3. If the user does not provide the details (task/model/dataset/metric), you should always suggest them.
        4. You should provide the paper reference of the task/model/algorithm/metric you suggest. You use the search
         results from the function `search_arxiv` or `search_papers_with_code` by generated search keywords.
        5. The suggestion should be as detailed as possible, include the SOTA methods for data processing, feature
         extraction, model selection, training/sering methods and evaluation metrics. And the reasons why you suggest.
        """
        self.ask_prompt = """
        You are an Machine learning expert, now you are talking to the user to help them write better ML project
         requirements.
         
        Your capabilities include:
        1. Read the user requirements and trying to understand the user's intent.
        2. Decide if the requirement is clear enough or not. If not clear, you should ask the user to provide more
         details.
        3. It is ok for the users to provide unclear answers (e.g., "No" or "I don't know"), but you job is to help
         user understand the goal that the user wants to achieve, and with as more as details.
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
        6. You should also use function `web_search` to search for articles, papers, or tutorials related to the
         task/model/algorithm/metric to help you decide which one to use.
        """
        self.json_mode_prompt = """

        Example JSON output:
        
        {
            "task":"text-classification",
            "model_or_algorithm":"BERT-base",
            "reference": ["https://arxiv.org/abs/1810.04805"],
            "evaluation_metric": ["accuracy", "f1"],
            "training_method": "fine-tuning",
            "serving_method": "Serving is not required",
            "device": "Local CPU",
            "suggestion": "Based on the user requirement, we suggest you to fine-tune a pre-trained BERT-base model for
            your text classification dataset. You can use the accuracy and f1 as the evaluation metrics."
        }
        
        {
            "task":"image-feature-extraction",
            "model_or_algorithm":"Pre-trained ResNet-50",
            "reference": ["https://arxiv.org/abs/2310.02037"],
            "evaluation_metric": ["accuracy"],
            "training_method": "Training is not required",
            "serving_method": "Serving is not required",
            "device": "GPU",
            "suggestion": "Based on the user's data and the requirement, we recommend using the pre-trained ResNet-50
             model to extract the features from the images, and use the accuracy as the evaluation metric. GPU is
              required for the feature extraction."
        }
        
        """
        self.functions = [schema_web_search, schema_search_arxiv, schema_search_papers_with_code]
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
                if answer.lower() in ["end", "exit"]:
                    return requirement

                self.ask_history.append({"role": "user", "content": answer})
                requirement += f"\nQuestion: {question}\nAnswer: {answer}"
                return self.ask(requirement)
            else:
                return self.ask(requirement)
        return requirement

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
