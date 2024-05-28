from abc import ABC, abstractmethod


class Model(ABC):

    def __init__(self):
        self.model_type = None

    @abstractmethod
    def query(self, chat_history):
        pass

    @abstractmethod
    def stream(self, chat_history):
        pass
