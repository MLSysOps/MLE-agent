import importlib.util
import re

from .common import Model


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
            self.model_type = 'Ollama'
            self.ollama = importlib.import_module(dependency)
            self.client = self.ollama.Client(host=host_url)
        else:
            raise ImportError(
                "It seems you didn't install ollama. In order to enable the Ollama client related features, "
                "please make sure ollama Python package has been installed. "
                "More information, please refer to: https://github.com/ollama/ollama-python"
            )

    def _clean_think_tags(self, text):
        """
        Remove content between <think> tags and empty think tags from the text.
        Args:
            text (str): The input text to clean.
        Returns:
            str: The cleaned text with think tags and their content removed.
        """
        # Remove content between <think> tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # Remove empty think tags
        text = re.sub(r'<think></think>', '', text)
        return text.strip()

    def _process_message(self, message, **kwargs):
        """
        Process the message before sending to the model.
        Args:
            message: The message to process.
            **kwargs: Additional arguments.
        Returns:
            dict: The processed message.
        """
        if isinstance(message, dict) and 'content' in message:
            message['content'] = self._clean_think_tags(message['content'])
        return message

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.
        Args:
            chat_history: The context (chat history).
            **kwargs: Additional arguments for the model.
        Returns:
            str: The model's response.
        """

        # Check if 'response_format' exists in kwargs
        format = None
        if 'response_format' in kwargs and kwargs['response_format'].get('type') == 'json_object':
            format = 'json'

        response = self.client.chat(model=self.model, messages=chat_history, format=format)
        return self._clean_think_tags(response['message']['content'])

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
            **kwargs: Additional arguments for the model.
        Yields:
            str: Chunks of the model's response.
        """

        for chunk in self.client.chat(
                model=self.model,
                messages=chat_history,
                stream=True
        ):
            yield self._clean_think_tags(chunk['message']['content'])
