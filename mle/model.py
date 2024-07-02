import importlib.util
from abc import ABC, abstractmethod


class Model(ABC):

    def __init__(self):
        """
        Initialize the model.
        """
        self.model_type = None

    @abstractmethod
    def query(self, chat_history, json_mode=False):
        pass

    @abstractmethod
    def stream(self, chat_history, json_mode=False):
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
            self.model_type = 'Ollama'
            self.ollama = importlib.import_module(dependency)
            self.client = self.ollama.Client(host=host_url)
        else:
            raise ImportError(
                "It seems you didn't install ollama. In order to enable the Ollama client related features, "
                "please make sure ollama Python package has been installed. "
                "More information, please refer to: https://github.com/ollama/ollama-python"
            )

    def query(self, chat_history, json_mode=False):
        """
        Query the LLM model.
        Args:
            chat_history: The context (chat history).
            json_mode: The output format in a structured JSON format.
        """
        return self.client.chat(model=self.model, messages=chat_history)['message']['content']

    def stream(self, chat_history, json_mode=False):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
            json_mode: The output format in a structured JSON format.
        """
        for chunk in self.client.chat(
                model=self.model,
                messages=chat_history,
                stream=True
        ):
            yield chunk['message']['content']


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
        self.model_type = 'OpenAI'
        self.temperature = temperature
        self.client = self.openai(api_key=api_key)

    def query(self, chat_history, json_mode=False):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
            json_mode: The output format in a structured JSON format.

        """

        if json_mode:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=chat_history,
                temperature=self.temperature,
                stream=False,
                response_format={"type": "json_object"}
            )
        else:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=chat_history,
                temperature=self.temperature,
                stream=False
            )

        return completion.choices[0].message.content

    def stream(self, chat_history, json_mode=False):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
            json_mode: The output format in a structured JSON
        """
        if json_mode:
            for chunk in self.client.chat.completions.create(
                    model=self.model,
                    messages=chat_history,
                    temperature=self.temperature,
                    stream=True,
                    response_format={"type": "json_object"}
            ):
                yield chunk.choices[0].delta.content
        else:
            for chunk in self.client.chat.completions.create(
                    model=self.model,
                    messages=chat_history,
                    temperature=self.temperature,
                    stream=True
            ):
                yield chunk.choices[0].delta.content
