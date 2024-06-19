from .base import BaseAgent
from agent.utils import update_project_state


class ReproduceAgent(BaseAgent):

    def pmpt_scan_readme(self) -> str:
        """
        Scan the README file to detect the requirements of the project. And then generate a step-by-step guide to
        run the project.
        :return:
        """
        pass

    def pmpt_scan_code(self) -> str:
        """
        Scan code file to detect whether the code is a valid code file.
        :return:
        """
        pass

    def pmpt_locate_data(self) -> str:
        """
        Detect the dataset location and the format
        :return:
        """
        pass

    def invoke(self):
        update_project_state(self.project)
