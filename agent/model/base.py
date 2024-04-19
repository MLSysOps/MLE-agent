from abc import ABC, abstractmethod


class Model(ABC):

    def __init__(self):
        self.model_type = None

    @abstractmethod
    def completions(self, chat_history):
        pass
