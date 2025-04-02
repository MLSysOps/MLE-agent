import importlib.util
import json
import requests
from typing import List, Dict, Any, Optional

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.model.common import Model


class VLLMModel(Model):
    def __init__(self, base_url=None, model=None, temperature=0.7):
        """
        Initialize the VLLM model.
        Args:
            base_url (str): The URL of the VLLM server.
            model (str): The model name (should match what's loaded in VLLM server).
            temperature (float): The temperature value.
        """
        super().__init__()
        
        self.base_url = base_url or "http://localhost:8000/v1"
        self.model = model or "mistralai/Mistral-7B-Instruct-v0.3"
        self.model_type = 'VLLM'
        self.temperature = temperature
        self.func_call_history = []
        
        # Check if server is accessible
        try:
            response = requests.get(f"{self.base_url}/models")
            if response.status_code != 200:
                raise ConnectionError(f"Failed to connect to VLLM server at {self.base_url}")
            
            # Optional: Get actual loaded model list and check if our model exists
            available_models = response.json().get("data", [])
            model_ids = [model.get("id") for model in available_models]
            
            if available_models and self.model not in model_ids:
                # If specified model is not in available list, use first available model
                print(f"Warning: Model '{self.model}' not found in VLLM server. Available models: {model_ids}")
                if model_ids:
                    self.model = model_ids[0]
                    print(f"Using available model: {self.model}")
                
        except Exception as e:
            raise ConnectionError(f"Failed to connect to VLLM server at {self.base_url}: {str(e)}")

    def normalize_chat_history(self, chat_history):
        """
        Normalize the chat history to ensure proper message sequence.
        """
        normalized = []
        last_role = None
        
        for msg in chat_history:
            role = msg.get("role", "")
            
            # Handle system messages
            if role == "system":
                if normalized:  # System messages must be at the beginning
                    continue
                normalized.append(msg)
                continue
                
            # Ensure user/assistant alternation
            if role in ["user", "assistant"]:
                if last_role == role:  # Skip consecutive messages with same role
                    continue
                normalized.append(msg)
                last_role = role
                
            # Handle function messages
            elif role == "function":
                # Convert function return to assistant message
                normalized.append({
                    "role": "assistant",
                    "content": f"Function '{msg.get('name', '')}' returned: {msg.get('content', '')}"
                })
                last_role = "assistant"
        
        # Ensure conversation ends with user message
        if normalized and normalized[-1]["role"] == "assistant":
            normalized.pop()
            
        return normalized

    def query(self, chat_history, **kwargs):
        """
        Query the VLLM model.
        Args:
            chat_history: The chat history to provide context.
            **kwargs: Additional parameters to pass to the API.
        Returns:
            str: The model's response.
        """
        # Normalize chat history
        normalized_history = self.normalize_chat_history(chat_history)
        
        payload = {
            "model": self.model,
            "messages": normalized_history,
            "temperature": self.temperature,
            "stream": False
        }
        
        # 添加其他参数
        payload.update(kwargs)
        
        # 发送请求
        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload
        )
        
        if response.status_code == 200:
            completion = response.json()
            return completion["choices"][0]["message"]["content"]
        else:
            raise Exception(f"VLLM API error: {response.text}")

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        parameters = kwargs.copy()
        
        # VLLM uses OpenAI-compatible API
        payload = {
            "model": self.model,
            "messages": chat_history,
            "temperature": self.temperature,
            "stream": True
        }
        
        # Handle function calling if present in kwargs
        if "functions" in parameters:
            payload["functions"] = parameters.pop("functions")
        if "function_call" in parameters:
            payload["function_call"] = parameters.pop("function_call")
        if "tools" in parameters:
            payload["tools"] = parameters.pop("tools")
        if "tool_choice" in parameters:
            payload["tool_choice"] = parameters.pop("tool_choice")
            
        # Add any remaining parameters
        payload.update(parameters)
        
        response = requests.post(f"{self.base_url}/chat/completions", json=payload, stream=True)
        
        if response.status_code != 200:
            raise Exception(f"VLLM API error: {response.status_code}")
            
        arguments = ''
        function_name = ''
        
        for line in response.iter_lines():
            if not line:
                continue
                
            if line.startswith(b"data: "):
                data = line[6:] 
                if data == b"[DONE]":
                    break
                    
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"]
                    
                    if "function_call" in delta:
                        if "name" in delta["function_call"]:
                            function_name = process_function_name(delta["function_call"]["name"])
                        if "arguments" in delta["function_call"]:
                            arguments += delta["function_call"]["arguments"]
                            
                    if chunk["choices"][0].get("finish_reason") == "function_call":
                        result = get_function(function_name)(**json.loads(arguments))
                        chat_history.append({"role": "function", "content": result, "name": function_name})
                        yield from self.stream(chat_history, **kwargs)
                    else:
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                except Exception as e:
                    print(f"Error processing stream: {e}")
