import importlib.util
import json

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.model.common import Model


class MistralModel(Model):
    def __init__(self, api_key, model, temperature=0.7):
        """
        Initialize the Mistral model.
        Args:
            api_key (str): The Mistral API key.
            model (str): The model with version.
            temperature (float): The temperature value.
        """
        super().__init__()

        dependency = "mistralai"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.mistral = importlib.import_module(dependency).Mistral
        else:
            raise ImportError(
                "It seems you didn't install mistralai. In order to enable the Mistral AI client related features, "
                "please make sure mistralai Python package has been installed. "
                "More information, please refer to: https://github.com/mistralai/client-python"
            )

        self.model = model if model else 'mistral-large-latest'
        self.model_type = 'MistralAI'
        self.temperature = temperature
        self.client = self.mistral(api_key=api_key)
        self.func_call_history = []

    def _convert_functions_to_tools(self, functions):
        """
        Convert OpenAI-style functions to Mistral-style tools.
        """
        tools = []
        for func in functions:
            tool = {
                "type": "function",
                "function": {
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": func["parameters"]
                }
            }
            tools.append(tool)
        return tools

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
        """
        functions = kwargs.get("functions",[])
        tools = self._convert_functions_to_tools(functions)
        tool_choice = kwargs.get('tool_choice', 'any')
        parameters = kwargs
        completion = self.client.chat.complete(
            model=self.model,
            messages=chat_history,
            temperature=self.temperature,
            stream=False,
            tools=tools,
            tool_choice=tool_choice,
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
        functions = kwargs.get("functions",[])
        tools = self._convert_functions_to_tools(functions)
        tool_choice = kwargs.get('tool_choice', 'any')
        for chunk in self.client.chat.complete(
            model=self.model,
            messages=chat_history,
            temperature=self.temperature,
            stream=True,
            tools=tools,
            tool_choice=tool_choice
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
