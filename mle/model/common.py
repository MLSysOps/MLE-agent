from abc import ABC, abstractmethod


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
