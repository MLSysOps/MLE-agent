import io
import os
import yaml
import json
import time
import importlib.util
from abc import ABC, abstractmethod

from mle.function import get_function, process_function_name

MODEL_OLLAMA = 'Ollama'
MODEL_OPENAI = 'OpenAI'


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
    def __init__(self, model: str = 'llama3', host_url=None):
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
            self.model = model
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
        return self.client.chat(model=self.model, messages=chat_history)['message']['content']

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


    def batch(self, chat_histories, **kwargs):
        """
        Batch query the LLM model.
        Args:
            chat_histories: The context list (chat history).
        """
        raise NotImplementedError("ollama does not support batch query")


class OpenAIModel(Model):
    def __init__(self, api_key, model='gpt-3.5-turbo', temperature=0.7):
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

        self.model = model
        self.model_type = MODEL_OPENAI
        self.temperature = temperature
        self.client = self.openai(api_key=api_key)

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
        """
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

    def batch(self, chat_histories, **kwargs):
        """
        Batch query the LLM model.
        Args:
            chat_histories: The context list (chat history).
        """
        chat_histories = [
            {
                "custom_id": f"request-{idx}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": self.model, "messages": message},
            }
            for idx, message in enumerate(chat_histories)
        ]

        file = io.BytesIO()
        for chat_history in chat_histories:
            file.write((json.dumps(chat_history) + "\n").encode("utf-8"))

        batch_file = self.client.files.create(file=file, purpose="batch")
        batch_id = self.client.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            **kwargs,
        ).id

        get_status = lambda batch_id: self.client.batches.retrieve(batch_id).status
        while get_status(batch_id) != "completed":
            if get_status(batch_id) in ("failed", "expired", "cancelling", "cancelled"):
                raise RuntimeError("Batch query failed")
            time.sleep(1)

        response_id = self.client.batches.retrieve(batch_id).output_file_id
        response = self.client.files.content(response_id).text

        return tuple([
            json.loads(text)["response"]["body"]["choices"][-1]["message"]["content"]
            for text in response.splitlines()
        ])

def load_model(project_dir: str, model_name: str):
    """
    load_model: load the model based on the configuration.
    Args:
        project_dir (str): The project directory.
        model_name (str): The model name.
    """
    with open(os.path.join(project_dir, 'project.yml'), 'r') as file:
        data = yaml.safe_load(file)
        if data['platform'] == MODEL_OPENAI:
            return OpenAIModel(api_key=data['api_key'], model=model_name)
        if data['platform'] == MODEL_OLLAMA:
            return OllamaModel(model=model_name)
    return None
