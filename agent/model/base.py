from abc import ABC, abstractmethod


class Model(ABC):

    def __init__(self):
        self.model_type = None

    @abstractmethod
    def load_data(self, data):
        pass

    @abstractmethod
    def load_model(self, model_path):
        pass
