import os
import copy
import importlib.util
import json
from abc import ABC, abstractmethod
from typing import Optional

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.utils import get_config

MODEL_OLLAMA = 'Ollama'
MODEL_OPENAI = 'OpenAI'
MODEL_CLAUDE = 'Claude'
MODEL_MISTRAL = 'MistralAI'
MODEL_DEEPSEEK = 'DeepSeek'

class Model(ABC):

    def __init__(self):
        """
        Initialize the model.
        """
        self.model_type = None

    @abstractmethod
    def query(self, chat_history, **kwargs):
        pass

    @abstractmethod
    def stream(self, chat_history, **kwargs):
        pass


class OllamaModel(Model):
    def __init__(self, model, host_url=None):
        """
        Initialize the Ollama model.
        Args:
            host_url (str): The Ollama Host url.
            model (str): The model version.
        """
        super().__init__()

        dependency = "ollama"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.model = model if model else 'llama3'
            self.model_type = MODEL_OLLAMA
            self.ollama = importlib.import_module(dependency)
            self.client = self.ollama.Client(host=host_url)
        else:
            raise ImportError(
                "It seems you didn't install ollama. In order to enable the Ollama client related features, "
                "please make sure ollama Python package has been installed. "
                "More information, please refer to: https://github.com/ollama/ollama-python"
            )

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.
        Args:
            chat_history: The context (chat history).
        """

        # Check if 'response_format' exists in kwargs
        format = None
        if 'response_format' in kwargs and kwargs['response_format'].get('type') == 'json_object':
            format = 'json'

        return self.client.chat(model=self.model, messages=chat_history, format=format)['message']['content']

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        for chunk in self.client.chat(
                model=self.model,
                messages=chat_history,
                stream=True
        ):
            yield chunk['message']['content']


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
        self.model_type = MODEL_OPENAI
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


class ClaudeModel(Model):
    def __init__(self, api_key, model, temperature=0.7):
        """
        Initialize the Claude model.
        Args:
            api_key (str): The Anthropic API key.
            model (str): The model with version.
            temperature (float): The temperature value.
        """
        super().__init__()

        dependency = "anthropic"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.anthropic = importlib.import_module(dependency).Anthropic
        else:
            raise ImportError(
                "It seems you didn't install anthropic. In order to enable the OpenAI client related features, "
                "please make sure openai Python package has been installed. "
                "More information, please refer to: https://docs.anthropic.com/en/api/client-sdks"
            )

        self.model = model if model else 'claude-3-5-sonnet-20240620'
        self.model_type = MODEL_CLAUDE
        self.temperature = temperature
        self.client = self.anthropic(api_key=api_key)
        self.func_call_history = []

    @staticmethod
    def _add_tool_result_into_chat_history(chat_history, func, result):
        """
        Add the result of tool calls into messages.
        """
        return chat_history.extend([
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": func.id,
                        "name": func.name,
                        "input": func.input,
                    },
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": func.id,
                        "content": result,
                    },
                ]
            },
        ])

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
        """
        # claude has not system role in chat_history
        # https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts
        system_prompt = ""
        for idx, msg in enumerate(chat_history):
            if msg["role"] == "system":
                system_prompt += msg["content"]

        # claude does not support mannual `response_format`, so we append it into system prompt
        if "response_format" in kwargs.keys():
            system_prompt += (
                f"\nOutputs only valid {kwargs['response_format']['type']} without any explanatory words"
            )

        # mapping the openai function_schema to claude tool_schema
        tools = kwargs.get("functions",[])
        for tool in tools:
            if "parameters" in tool.keys():
                tool["input_schema"] = tool["parameters"]
                del tool["parameters"]

        completion = self.client.messages.create(
            max_tokens=4096,
            model=self.model,
            system=system_prompt,
            messages=[msg for msg in chat_history if msg["role"] != "system"],
            temperature=self.temperature,
            stream=False,
            tools=tools,
        )
        if completion.stop_reason == "tool_use":
            for func in completion.content:
                if func.type != "tool_use":
                    continue
                function_name = process_function_name(func.name)
                arguments = func.input
                print("[MLE FUNC CALL]: ", function_name)
                self.func_call_history.append({"name": function_name, "arguments": arguments})
                # avoid the multiple search function calls
                search_attempts = [item for item in self.func_call_history if item['name'] in SEARCH_FUNCTIONS]
                if len(search_attempts) > 3:
                    kwargs['functions'] = []
                result = get_function(function_name)(**arguments)
                self._add_tool_result_into_chat_history(chat_history, func, result)
                return self.query(chat_history, **kwargs)
        else:
            return completion.content[0].text

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        # claude has not system role in chat_history
        # https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts
        system_prompt = ""
        for idx, msg in enumerate(chat_history):
            if msg["role"] == "system":
                system_prompt += msg["content"]
        chat_history = [msg for msg in chat_history if msg["role"] != "system"]

        # claude does not support mannual `response_format`, so we append it into system prompt
        if "response_format" in kwargs.keys():
            system_prompt += (
                f"\nOutputs only valid {kwargs['response_format']['type']} without any explanatory words"
            )

        with self.client.messages.stream(
            max_tokens=4096,
            model=self.model,
            messages=chat_history,
        ) as stream:
            for chunk in stream.text_stream:
                yield chunk

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
        self.model_type = MODEL_MISTRAL
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
        self.model_type = MODEL_DEEPSEEK
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


class ObservableModel:
    """
    A class that wraps a model to make it trackable by the metric platform (e.g., Langfuse).
    """

    try:
        from mle.utils import get_langfuse_observer
        _observe = get_langfuse_observer()
    except Exception as e:
        # If importing fails, set _observe to a lambda function that does nothing.
        _observe = lambda fn: fn

    def __init__(self, model: Model):
        """
        Initialize the ObservableModel.
        Args:
            model: The model to be wrapped and made observable.
        """
        self.model = model

    @_observe
    def query(self, *args, **kwargs):
        return self.model.query(*args, **kwargs)

    @_observe
    def stream(self, *args, **kwargs):
        return self.model.query(*args, **kwargs)


def load_model(project_dir: str, model_name: Optional[str]=None, observable=True):
    """
    load_model: load the model based on the configuration.
    Args:
        project_dir (str): The project directory.
        model_name (str): The model name.
        observable (boolean): Whether the model should be tracked.
    """
    config = get_config(project_dir)
    model = None

    if config['platform'] == MODEL_OLLAMA:
        model = OllamaModel(model=model_name)
    if config['platform'] == MODEL_OPENAI:
        model = OpenAIModel(api_key=config['api_key'], model=model_name)
    if config['platform'] == MODEL_CLAUDE:
        model = ClaudeModel(api_key=config['api_key'], model=model_name)
    if config['platform'] == MODEL_MISTRAL:
        model = MistralModel(api_key=config['api_key'], model=model_name)
    if config['platform'] == MODEL_DEEPSEEK:
        model = DeepSeekModel(api_key=config['api_key'], model=model_name)

    if observable:
        return ObservableModel(model)
    return model
