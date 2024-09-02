import os
import yaml
import json
import importlib.util
from abc import ABC, abstractmethod

from mle.function import get_function, process_function_name

MODEL_OLLAMA = 'Ollama'
MODEL_OPENAI = 'OpenAI'
MODEL_CLAUDE = 'Claude'

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

        self.model = model if model else 'gpt-4o'
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
        chat_history = [msg for msg in chat_history if msg["role"] != "system"]

        # claude does not support mannual `response_format`, so we append it into system prompt
        if "response_format" in kwargs.keys():
            system_prompt += (
                f"\nYou must output in {kwargs['response_format']['type']} format"
                "Json format example: {\"key\": \"value\n value\n\"})")
            chat_history.append({
                "role": "assistant",
                "content": f"Raw text output in {kwargs['response_format']['type']} format:"
            })

        completion = self.client.messages.create(
            max_tokens=4096,
            model=self.model,
            system=system_prompt,
            messages=chat_history,
            temperature=self.temperature,
            stream=False
        )

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
                f"\nYou must output in {kwargs['response_format']['type']} format."
                "Json format example: {\"key\": \"import a\n print(a)\n\"})")
            chat_history.append({
                "role": "assistant",
                "content": f"Raw text output in {kwargs['response_format']['type']} format:"
            })

        with self.client.messages.stream(
            max_tokens=4096,
            model=self.model,
            messages=chat_history,
        ) as stream:
            for chunk in stream.text_stream:
                yield chunk


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
        if data['platform'] == MODEL_CLAUDE:
            return ClaudeModel(api_key=data['api_key'], model=model_name)
        if data['platform'] == MODEL_OLLAMA:
            return OllamaModel(model=model_name)
    return None
