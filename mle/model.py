import os
import yaml
import json
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from mle.utils import process_function_name  # Adjust the import path as needed

MODEL_OLLAMA = 'Ollama'
MODEL_OPENAI = 'OpenAI'

class Model(ABC):
    def __init__(self):
        self.model_type: Optional[str] = None

    @abstractmethod
    def query(self, chat_history: List[Dict[str, str]], **kwargs) -> str:
        pass

    @abstractmethod
    def stream(self, chat_history: List[Dict[str, str]], **kwargs) -> str:
        pass

class OllamaModel(Model):
    def __init__(self, model: str = 'llama3', host_url: Optional[str] = None):
        super().__init__()
        self.model = model
        self.model_type = MODEL_OLLAMA
        self.ollama = self._import_ollama()
        self.client = self.ollama.Client(host=host_url)

    def _import_ollama(self):
        dependency = "ollama"
        spec = importlib.util.find_spec(dependency)
        if spec is None:
            raise ImportError(
                "Ollama Python package is not installed. "
                "Please install it to use Ollama-related features. "
                "More information: https://github.com/ollama/ollama-python"
            )
        return importlib.import_module(dependency)

    def query(self, chat_history: List[Dict[str, str]], **kwargs) -> str:
        return self.client.chat(model=self.model, messages=chat_history)['message']['content']

    def stream(self, chat_history: List[Dict[str, str]], **kwargs) -> str:
        for chunk in self.client.chat(model=self.model, messages=chat_history, stream=True):
            yield chunk['message']['content']

class OpenAIModel(Model):
    def __init__(self, api_key: str, model: str = 'gpt-3.5-turbo', temperature: float = 0.7):
        super().__init__()
        self.model = model
        self.model_type = MODEL_OPENAI
        self.temperature = temperature
        self.openai = self._import_openai()
        self.client = self.openai(api_key=api_key)

    def _import_openai(self):
        dependency = "openai"
        spec = importlib.util.find_spec(dependency)
        if spec is None:
            raise ImportError(
                "OpenAI Python package is not installed. "
                "Please install it to use OpenAI-related features. "
                "More information: https://openai.com/product"
            )
        return importlib.import_module(dependency).OpenAI

    def query(self, chat_history: List[Dict[str, str]], **kwargs) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=chat_history,
            temperature=self.temperature,
            stream=False,
            **kwargs
        )

        resp = completion.choices[0].message
        if resp.function_call:
            function_name = process_function_name(resp.function_call.name)
            arguments = json.loads(resp.function_call.arguments)
            print("[MLE FUNC CALL]: ", function_name)
            result = get_function(function_name)(**arguments)
            chat_history.append({"role": "function", "content": result, "name": function_name})
            return self.query(chat_history, **kwargs)
        else:
            return resp.content

    def stream(self, chat_history: List[Dict[str, str]], **kwargs) -> str:
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

def load_model(project_dir: str, model_name: str) -> Optional[Model]:
    with open(os.path.join(project_dir, 'project.yml'), 'r') as file:
        data = yaml.safe_load(file)
        if data['platform'] == MODEL_OPENAI:
            return OpenAIModel(api_key=data['api_key'], model=model_name)
        if data['platform'] == MODEL_OLLAMA:
            return OllamaModel(model=model_name)
    return None
