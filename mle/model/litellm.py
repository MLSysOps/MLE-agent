import os
import json
import importlib.util
from typing import List, Dict, Any, Optional

from mle.model.common import Model
from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name


class LiteLLMModel(Model):
    """
    LiteLLM model implementation using OpenAI-compatible API.

    LiteLLM is an AI gateway/proxy that provides a unified OpenAI-compatible
    interface to 100+ LLM providers (OpenAI, Anthropic, Azure, Bedrock,
    Vertex AI, Mistral, Cohere, etc.).

    See: https://docs.litellm.ai/
    """

    def __init__(self, api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: Optional[str] = None,
                 temperature: float = 0.7) -> None:
        """Initialize the LiteLLM model.

        Args:
            api_key: The LiteLLM proxy API key (master key or virtual key).
            base_url: The URL of the LiteLLM proxy server.
            model: The model name (e.g., gpt-4o, claude-3-5-sonnet).
            temperature: The sampling temperature.
        """
        super().__init__()

        dependency = "openai"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.openai = importlib.import_module(dependency).OpenAI
        else:
            raise ImportError(
                "OpenAI package not found. Please install it using: "
                "pip install openai"
            )

        self.model = model if model else "gpt-4o"
        self.model_type = 'LiteLLM'
        self.temperature = temperature
        self.client = self.openai(
            api_key=api_key or os.getenv("LITELLM_API_KEY", ""),
            base_url=base_url or os.getenv("LITELLM_BASE_URL",
                                           "http://localhost:4000/v1"),
            timeout=60.0,
            max_retries=2,
        )
        self.func_call_history = []

    def _convert_functions_to_tools(self, functions):
        """
        Convert OpenAI-style functions to tools format.
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

    def query(self, chat_history: List[Dict[str, Any]], **kwargs) -> str:
        """Query the LLM model.

        Args:
            chat_history: The context (chat history).
            **kwargs: Additional parameters for the API call.

        Returns:
            Model's response as string.
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
                chat_history.append({
                    "role": "assistant",
                    "content": '',
                    "tool_calls": [tool_call],
                    "prefix": False
                })
                function_name = process_function_name(tool_call.function.name)
                arguments = json.loads(tool_call.function.arguments)
                print("[MLE FUNC CALL]: ", function_name)
                self.func_call_history.append({
                    "name": function_name,
                    "arguments": arguments
                })
                search_attempts = [
                    item for item in self.func_call_history
                    if item['name'] in SEARCH_FUNCTIONS
                ]
                if len(search_attempts) > 3:
                    parameters['tool_choice'] = "none"
                result = get_function(function_name)(**arguments)
                chat_history.append({
                    "role": "tool",
                    "content": result,
                    "name": function_name,
                    "tool_call_id": tool_call.id
                })
                return self.query(chat_history, **parameters)
        else:
            return resp.content

    def stream(self, chat_history: List[Dict[str, Any]], **kwargs) -> str:
        """Stream the output from the LLM model.

        Args:
            chat_history: The context (chat history).
            **kwargs: Additional parameters for the API call.

        Yields:
            Chunks of the model's response.
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
                    chat_history.append({
                        "role": "assistant",
                        "content": '',
                        "tool_calls": [tool_call],
                        "prefix": False
                    })
                    function_name = process_function_name(tool_call.function.name)
                    arguments = json.loads(tool_call.function.arguments)
                    result = get_function(function_name)(**arguments)
                    chat_history.append({
                        "role": "tool",
                        "content": result,
                        "name": function_name
                    })
                    yield from self.stream(chat_history, **kwargs)
            else:
                yield chunk.choices[0].delta.content
