"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""

from mle.agents import CodeAgent, DebugAgent
from mle.model import load_model

if __name__ == '__main__':
    working_dir = '/Users/huangyz0918/desktop/test'
    requirement = "Create a Python program that solve leetcode problem 35, you may search the problem on the web."

    model = load_model(working_dir, 'gpt-4o')
    coder = CodeAgent(model)
    debugger = DebugAgent(model)

    print(f"Developer: {coder.handle_query(requirement, working_dir)}")
    print(f"Debugger: {debugger.handle_query(working_dir)}")
