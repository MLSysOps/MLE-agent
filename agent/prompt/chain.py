from agent.utils import load_yml_to_pydantic_model
from agent.types import Step


class Chain:

    def __init__(self, task_file: str):
        """
        Chain: the interactive chain of the current ML task.
        :param task_file: the path of the task file.
        """
        self.step = load_yml_to_pydantic_model(task_file, Step)

    def execute(self):
        """
        Execute the chain.
        :return: the result of the chain.
        """
        pass


if __name__ == '__main__':
    chain = Chain('../templates/data_collection.yml')
    print(chain.step.dict())
