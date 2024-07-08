"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
import textwrap
from mle.model import load_model
from mle.utils import print_in_box
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent


def baseline(work_dir: str):
    """
    The workflow of the baseline mode.
    :return:
    """
    ml_requirement = "I want to build an image classification model."
    print_in_box(ml_requirement, title="User", color="blue")
    model = load_model(work_dir, 'gpt-4o')

    advisor = AdviseAgent(model)
    suggestion = advisor.suggest(ml_requirement)
    enhanced_requirement = textwrap.dedent(f"""
    The user's requirement: {ml_requirement}
    The ML task: {suggestion.get('task')},
    The model: {suggestion.get('model')},
    The dataset: {suggestion.get('dataset')},
    The reference: {suggestion.get('reference')},
    The evaluation metric: {suggestion.get('evaluation_metric')}
    """)
    print_in_box(enhanced_requirement, title="Advisor", color="green")

    planner = PlanAgent(model)
    coding_plan = planner.plan(enhanced_requirement)
    plan_str = ""
    for task in coding_plan.get('tasks'):
        plan_str += f"[Task]: {task.get('task')}\n[Description]: {task.get('description')}\n\n"
    print_in_box(plan_str, title="Planner", color="purple")

    coder = CodeAgent(model, work_dir)
    debugger = DebugAgent(model)

    for current_task in coding_plan.get('tasks'):
        task_requirement = textwrap.dedent(f"""
        You are required to complete task: {current_task.get('task')}.\n
        You should: {current_task.get('description')}
        """)

        code_report = coder.code(task_requirement)
        code_prompt = textwrap.dedent(f"""
        I have finish the task: {current_task.get('task')}. {code_report.get('message')}\n
        The dependencies required to run the code: {code_report.get('dependency')}\n
        The command to run the code: {code_report.get('command')}\n
        Whether the code is required to execute and debug: {code_report.get('debug')}
        """)
        print_in_box(code_prompt, title="Developer", color="cyan")

        while True:
            is_debugging = code_report.get('debug')
            if is_debugging == 'true' or is_debugging == 'True':
                debug_report = debugger.analyze(code_prompt)
                if debug_report.get('status') == 'success':
                    print_in_box(f"debug with {debug_report.get('status')}", title="Debugger", color="yellow")
                    break
                else:
                    improve_prompt = textwrap.dedent(f"""
                    You are required improve the existing project.\n
                    The required changes: {debug_report.get("changes")}\n
                    The suggestion: {debug_report.get("suggestion")}
                    
                    """)
                    print_in_box(improve_prompt, title="Debugger", color="yellow")
                    code_report = coder.code(improve_prompt)
            else:
                break
