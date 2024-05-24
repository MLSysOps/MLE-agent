import importlib.util

from agent.types.const import LLM_TYPE_OPENAI
from .base import Model


class OpenAIModel(Model):
    def __init__(self, api_key, model, temperature):
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
            self.OpenAI = importlib.import_module(dependency).OpenAI
            self.RateLimitError = importlib.import_module(dependency).RateLimitError
        else:
            raise ImportError(
                "It seems you didn't install openai. In order to enable the OpenAI client related features, "
                "please make sure openai Python package has been installed. "
                "More information, please refer to: https://openai.com/product"
            )

        self.model = model
        self.model_type = LLM_TYPE_OPENAI
        self.temperature = temperature
        self.client = self.OpenAI(api_key=api_key)

    def completions(
            self,
            chat_history,
            stream=True
    ):
        """
        Completions of the LLM model.
        Args:
            chat_history: The context (chat history).
            stream: The flag to stream the output.
        """

        return self.client.chat.completions.create(
            model=self.model,
            messages=chat_history,
            temperature=self.temperature,
            stream=stream
        )