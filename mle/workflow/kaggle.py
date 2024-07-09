"""
Kaggle Mode: the mode to run the kaggle competition automatically.

TODO: @Huaizheng - Write the workflow and use the agents to run the kaggle competition automatically.
"""
import os
import questionary

from mle.model import load_model
from mle.utils import print_in_box
from mle.agents import AdviseAgent


def kaggle():
    ml_requirement = questionary.text("Your requirement:").ask()
    if not ml_requirement:
        print_in_box("The user's requirement is empty. Aborted", title="Error", color="red")
        return

    model = load_model(os.getcwd(), 'gpt-4o')
    advisor = AdviseAgent(model)

    print(advisor.ask(ml_requirement))
    # print_in_box(json.dumps(advisor.suggest(ml_requirement)), title="Advisor", color="green")
