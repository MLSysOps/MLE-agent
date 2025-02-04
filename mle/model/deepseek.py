import re
import os
import json
import logging
import importlib.util
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

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
        self.model = model if model else "reasoning_content"
        self.model_type = 'DeepSeek'
        self.temperature = temperature
        self.client = self.openai(
            api_key=api_key, base_url="https://api.deepseek.com"
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
        if "reasoning_content" in self.model or "deepseek-r1" in self.model:
            # https://api-docs.deepseek.com/guides/reasoning_model
            if "functions" in kwargs:
                kwargs.pop("functions")
                logging.warning("DeepSeek R1 does not support function call.")

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
            thinking = ""
            completion = ""

            if hasattr(resp, "reasoning_content"):
                thinking = resp.reasoning_content
                completion = resp.content
            else:
                pattern_match = re.match(r"(?:<think>(.*?)</think>)?(.*)", resp.content, re.DOTALL)
                if pattern_match:
                    thinking = pattern_match.group(1) if pattern_match.group(1) is not None else ""
                    completion = pattern_match.group(2) if pattern_match.group(2) is not None else ""

            if os.getenv("MLE_DEBUG", "False") == "True":
                with Live(console=Console()) as live:
                    live.update(
                        Panel(
                            Markdown(thinking.strip(), style="dim"),
                            title="[bold]DeepSeek Thinking[/bold]",
                            border_style="grey50",
                            style="dim",
                        ), refresh=True)

            return completion.strip()

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        if "reasoning_content" in self.model or "deepseek-r1" in self.model:
            # https://api-docs.deepseek.com/guides/reasoning_model
            if "functions" in kwargs:
                kwargs.pop("functions")
                logging.warning("DeepSeek R1 does not support function call.")

        arguments = ""
        function_name = ""
        thinking_content = ""
        thinking_console = Live(console=Console())
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
                if hasattr(chunk.choices[0].delta, "reasoning_content"):
                    thinking_content += chunk.choices[0].delta.reasoning_content
                    if os.getenv("MLE_DEBUG", "False") == "True":
                        thinking_console.update(Panel(
                            Markdown(thinking_content.strip(), style="dim"),
                            title="[bold]DeepSeek Thinking[/bold]",
                            border_style="grey50",
                            style="dim",
                        ), refresh=True)
                else:
                    yield chunk.choices[0].delta.content
