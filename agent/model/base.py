from abc import ABC, abstractmethod


class Model(ABC):

    def __init__(self):
        self.model_type = None

    @abstractmethod
    def chat(self, context: str, text: str):
        pass
