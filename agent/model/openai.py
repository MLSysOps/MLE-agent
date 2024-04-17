import importlib.util

from .base import Model


class OpenAIModel(Model):
    def __init__(self, api_key, version, temperature):
        """
        Initialize the OpenAI model.
        Args:
            api_key (str): The OpenAI API key.
            version (str): The model version.
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

        self.version = version
        self.temperature = temperature
        self.client = self.OpenAI(api_key=api_key)

    def load_data(self, data):
        pass

    def load_model(self, model_path):
        pass
