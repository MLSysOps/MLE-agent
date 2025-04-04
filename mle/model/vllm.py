import os
import importlib.util
import json
from typing import List, Dict, Any, Optional

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.model.common import Model


class VLLMModel(Model):
    """VLLM model implementation using OpenAI-compatible API."""

    def __init__(self, base_url: Optional[str] = None,
                 model: Optional[str] = None,
                 temperature: float = 0.7) -> None:
        """Initialize the VLLM model.

        Args:
            base_url: The URL of the VLLM server.
            model: The model name.
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

        self.model = model if model else 'mistralai/Mistral-7B-Instruct-v0.3'
        self.model_type = 'VLLM'
        self.temperature = temperature
        self.client = self.openai(
            api_key="EMPTY",  
            base_url=base_url or os.getenv("VLLM_BASE_URL",
                                         "http://localhost:8000/v1"),
            timeout=60.0,
            max_retries=2,
        )
        self.func_call_history = []

    def normalize_chat_history(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize chat history to ensure it follows the required format.

        Args:
            chat_history: The original chat history.

        Returns:
            Normalized chat history list.
        """
        normalized = []

        # Handle system message first
        system_messages = [msg for msg in chat_history if msg["role"] == "system"]
        if system_messages:
            normalized.append(system_messages[0])

        # Add other messages in order
        for msg in chat_history:
            if msg["role"] == "system":
                continue

            if msg["role"] in ["user", "assistant", "function"]:
                normalized.append(msg)

        return normalized

    def query(self, chat_history: List[Dict[str, Any]], **kwargs) -> str:
        """Query the LLM model.

        Args:
            chat_history: The context (chat history).
            **kwargs: Additional parameters for the API call.

        Returns:
            Model's response as string.

        Raises:
            Exception: If the API call fails.
        """
        try:
            normalized_history = self.normalize_chat_history(chat_history)
            parameters = kwargs
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=normalized_history,
                temperature=self.temperature,
                stream=False,
                **parameters
            )

            resp = completion.choices[0].message
            if resp.function_call:
                function_name = process_function_name(resp.function_call.name)
                arguments = json.loads(resp.function_call.arguments)
                print("[MLE FUNC CALL]: ", function_name)
                self.func_call_history.append({
                    "name": function_name,
                    "arguments": arguments
                })

                # Avoid multiple search function calls
                search_attempts = [
                    item for item in self.func_call_history
                    if item['name'] in SEARCH_FUNCTIONS
                ]
                if len(search_attempts) > 3:
                    parameters['function_call'] = "none"

                result = get_function(function_name)(**arguments)
                chat_history.append({
                    "role": "assistant",
                    "function_call": dict(resp.function_call)
                })
                chat_history.append({
                    "role": "function",
                    "content": result,
                    "name": function_name
                })
                return self.query(chat_history, **parameters)
            return resp.content

        except Exception as e:
            error_msg = f"VLLM API error: {str(e)}"
            print(f"Error during VLLM query: {error_msg}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise Exception(error_msg)

    def stream(self, chat_history: List[Dict[str, Any]], **kwargs) -> str:
        """Stream the output from the LLM model.

        Args:
            chat_history: The context (chat history).
            **kwargs: Additional parameters for the API call.

        Yields:
            Chunks of the model's response.

        Raises:
            Exception: If the streaming fails.
        """
        try:
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
                        function_name = process_function_name(
                            delta.function_call.name
                        )
                    if delta.function_call.arguments:
                        arguments += delta.function_call.arguments

                if chunk.choices[0].finish_reason == "function_call":
                    result = get_function(function_name)(**json.loads(arguments))
                    chat_history.append({
                        "role": "function",
                        "content": result,
                        "name": function_name
                    })
                    yield from self.stream(chat_history, **kwargs)
                else:
                    yield delta.content

        except Exception as e:
            error_msg = f"VLLM streaming error: {str(e)}"
            print(f"Error during VLLM streaming: {error_msg}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise Exception(error_msg)
