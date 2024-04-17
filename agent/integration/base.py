from abc import ABC, abstractmethod


class Integration(ABC):

    def __init__(self):
        self.integration_type = None

    @abstractmethod
    def get_credentials(self):
        pass
