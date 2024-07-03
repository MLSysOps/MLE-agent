"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
from mle.agents import CodeAgent, DebugAgent
from mle.model import load_model


def baseline():
    """
    The workflow of the baseline mode.
    :return:
    """
    working_dir = '/Users/huangyz0918/desktop/test'
    requirement = "Create a Python program that solve LeetCode problem 102, you may search the problem on the web."

    model = load_model(working_dir, 'gpt-4o')
    coder = CodeAgent(model, working_dir)
    debugger = DebugAgent(model)

    print(f"Developer: {coder.code(requirement)}")
    print(f"Debugger: {debugger.analyze(working_dir)}")
