import importlib.util
import json

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.model.common import Model


class DeepSeekModel(Model):
    def __init__(self, api_key, model, temperature=0.7):
        """
        Initialize the DeepSeek model.
        Args:
            api_key (str): The DeepSeek API key.
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
        self.model = model if model else "deepseek-coder"
        self.model_type = 'DeepSeek'
        self.temperature = temperature
        self.client = self.openai(
            api_key=api_key, base_url="https://api.deepseek.com/beta"
        )
        self.func_call_history = []

    def _convert_functions_to_tools(self, functions):
        """
        Convert OpenAI-style functions to DeepSeek-style tools.
        """
        tools = []
        for func in functions:
            tool = {
                "type": "function",
                "function": {
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": func["parameters"],
                },
            }
            tools.append(tool)
        return tools

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
        """
        functions = kwargs.get("functions", None)
        tools = self._convert_functions_to_tools(functions) if functions else None
        parameters = kwargs
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=chat_history,
            temperature=self.temperature,
            stream=False,
            tools=tools,
            **parameters,
        )

        resp = completion.choices[0].message
        if resp.tool_calls:
            for tool_call in resp.tool_calls:
                chat_history.append({"role": "assistant", "content": '', "tool_calls": [tool_call], "prefix":False})
                function_name = process_function_name(tool_call.function.name)
                arguments = json.loads(tool_call.function.arguments)
                print("[MLE FUNC CALL]: ", function_name)
                self.func_call_history.append({"name": function_name, "arguments": arguments})
                # avoid the multiple search function calls
                search_attempts = [item for item in self.func_call_history if item['name'] in SEARCH_FUNCTIONS]
                if len(search_attempts) > 3:
                    parameters['tool_choice'] = "none"
                result = get_function(function_name)(**arguments)
                chat_history.append({"role": "tool", "content": result, "name": function_name, "tool_call_id":tool_call.id})
                return self.query(chat_history, **parameters)
        else:
            return resp.content

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        arguments = ""
        function_name = ""
        for chunk in self.client.chat.completions.create(
            model=self.model,
            messages=chat_history,
            temperature=self.temperature,
            stream=True,
            **kwargs,
        ):
            if chunk.choices[0].delta.tool_calls:
                tool_call = chunk.choices[0].delta.tool_calls[0]
                if tool_call.function.name:
                    chat_history.append({"role": "assistant", "content": '', "tool_calls": [tool_call], "prefix":False})
                    function_name = process_function_name(tool_call.function.name)
                    arguments = json.loads(tool_call.function.arguments)
                    result = get_function(function_name)(**arguments)
                    chat_history.append({"role": "tool", "content": result, "name": function_name})
                    yield from self.stream(chat_history, **kwargs)
            else:
                yield chunk.choices[0].delta.content
