import importlib.util

from .base import Model
from agent.const import LLM_TYPE_OPENAI


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

    def chat(self, context: str, text: str):
        """
        Chat with the model.
        Args:
            context (str): The context (chat history) prompt.
            text (str): The text prompt.
        """
        try:
            chat_history = [
                {"role": "system", "content": context},
                {"role": "user", "content": text}
            ]

            completion = self.client.chat.completions.create(
                model=self.version,
                messages=chat_history,
                temperature=self.temperature
            )

            response = completion.choices[0].message.content
            return response
        except self.RateLimitError as e:
            print("Rate limit exceeded. Please try again later.")
            print(f"Error message: {e}")
        except Exception as e:
            print("OpenAI error occurred.")
            print(f"Error message: {e}")
