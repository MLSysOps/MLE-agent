"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
import json
from mle.model import load_model
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent


def baseline(work_dir: str):
    """
    The workflow of the baseline mode.
    :return:
    """
    ml_requirement = """
    I want to build a baseline for the continue learning method of the spoken keyword spotting task.
    """

    print(f"User: {ml_requirement}")
    model = load_model(work_dir, 'gpt-4o')

    advisor = AdviseAgent(model)
    suggestion = advisor.suggest(ml_requirement)
    print(f"Advisor: {suggestion}")

    planner = PlanAgent(model)
    coding_plan = planner.plan(ml_requirement + suggestion)
    print(f"Planner: {coding_plan}")

    coder = CodeAgent(model, work_dir)
    debugger = DebugAgent(model)

    while True:
        code_report = coder.code(coding_plan)
        print(f"Developer: {code_report}")
        debug_report = debugger.analyze(code_report)
        print(f"Debugger: {debug_report}")
        if json.loads(debug_report).get('status') == 'success':
            break
