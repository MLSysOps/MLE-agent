"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
import textwrap
import questionary
from rich.console import Console
from mle.model import load_model
from mle.utils import print_in_box
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent


def baseline(work_dir: str, model='gpt-4o'):
    """
    The workflow of the baseline mode.
    :return:
    """

    console = Console()
    ml_requirement = questionary.text("Your requirement:").ask()
    if not ml_requirement:
        print_in_box("The user's requirement is empty. Aborted", console, title="Error", color="red")
        return

    print_in_box(ml_requirement, console, title="User")
    model = load_model(work_dir, model)

    print_in_box("I am going to ask your several questions to understand your requirements better, "
                 "if you don't want to answer or have no idea, you can reply \"no\" or \"I don't know\"."
                 " To end the question, you can reply \"end\" or \"exit\".",
                 console, title="MLE Advisor", color="green")

    advisor = AdviseAgent(model)
    requirement_with_qa = advisor.ask(ml_requirement)

    with console.status("Advisor is thinking the suggestion for the requirements..."):
        suggestion = advisor.suggest(requirement_with_qa)
        enhanced_requirement = textwrap.dedent(f"""
        The user's requirement: {ml_requirement}\n
        The ML task: {suggestion.get('task')},
        The model: {suggestion.get('model')},
        The dataset: {suggestion.get('dataset')},
        The reference: {suggestion.get('reference')},
        The evaluation metric: {suggestion.get('evaluation_metric')},
        The suggestion: {suggestion.get('suggestion')}
        """)
        print_in_box(enhanced_requirement, console, title="MLE Advisor", color="green")

    with console.status("Planner is planning the coding tasks..."):
        planner = PlanAgent(model)
        coding_plan = planner.plan(enhanced_requirement)
        plan_str = ""
        for task in coding_plan.get('tasks'):
            plan_str += f"[Task]: {task.get('task')}\n[Description]: {task.get('description')}\n\n"
        print_in_box(plan_str, console, title="MLE Planner", color="purple")

    coder = CodeAgent(model, work_dir)
    debugger = DebugAgent(model)

    for current_task in coding_plan.get('tasks'):
        with console.status(f"Coder is coding the tasks: {current_task.get('task')}"):
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
            print_in_box(code_prompt, console, title="MLE Developer", color="cyan")

        while True:
            is_debugging = code_report.get('debug')
            if is_debugging == 'true' or is_debugging == 'True':
                with console.status("Debugger is executing and debugging the code..."):
                    debug_report = debugger.analyze(code_prompt)

                if debug_report.get('status') == 'success':
                    print_in_box(f"debug with {debug_report.get('status')}", console, title="Debugger", color="yellow")
                    break
                else:
                    improve_prompt = textwrap.dedent(f"""
                    You are required improve the existing project.\n
                    The required changes: {debug_report.get("changes")}\n
                    The suggestion: {debug_report.get("suggestion")}
                    
                    """)
                    print_in_box(improve_prompt, console, title="MLE Debugger", color="yellow")
                    with console.status("Coder is improving the code..."):
                        code_report = coder.code(improve_prompt)
            else:
                break
