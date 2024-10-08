import os
import importlib.util
import json

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.model.common import Model


class OpenAIModel(Model):
    def __init__(self, api_key, model, temperature=0.7):
        """
        Initialize the OpenAI model.
        Args:
            api_key (str): The OpenAI API key.
            model (str): The model with version.
            temperature (float): The temperature value.
        """
        super().__init__()

        dependency = "openai"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.openai = importlib.import_module(dependency).OpenAI
        else:
            raise ImportError(
                "It seems you didn't install openai. In order to enable the OpenAI client related features, "
                "please make sure openai Python package has been installed. "
                "More information, please refer to: https://openai.com/product"
            )

        self.model = model if model else 'gpt-4o-2024-08-06'
        self.model_type = 'OpenAI'
        self.temperature = temperature
        self.client = self.openai(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        self.func_call_history = []

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
        """
        parameters = kwargs
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=chat_history,
            temperature=self.temperature,
            stream=False,
            **parameters
        )

        resp = completion.choices[0].message
        if resp.function_call:
            function_name = process_function_name(resp.function_call.name)
            arguments = json.loads(resp.function_call.arguments)
            print("[MLE FUNC CALL]: ", function_name)
            self.func_call_history.append({"name": function_name, "arguments": arguments})
            # avoid the multiple search function calls
            search_attempts = [item for item in self.func_call_history if item['name'] in SEARCH_FUNCTIONS]
            if len(search_attempts) > 3:
                parameters['function_call'] = "none"
            result = get_function(function_name)(**arguments)
            chat_history.append({"role": "assistant", "function_call": dict(resp.function_call)})
            chat_history.append({"role": "function", "content": result, "name": function_name})
            return self.query(chat_history, **parameters)
        else:
            return resp.content

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        arguments = ''
        function_name = ''
        for chunk in self.client.chat.completions.create(
                model=self.model,
                messages=chat_history,
                temperature=self.temperature,
                stream=True,
                **kwargs
        ):
            delta = chunk.choices[0].delta
            if delta.function_call:
                if delta.function_call.name:
                    function_name = process_function_name(delta.function_call.name)
                if delta.function_call.arguments:
                    arguments += delta.function_call.arguments

            if chunk.choices[0].finish_reason == "function_call":
                result = get_function(function_name)(**json.loads(arguments))
                chat_history.append({"role": "function", "content": result, "name": function_name})
                yield from self.stream(chat_history, **kwargs)
            else:
                yield delta.content
