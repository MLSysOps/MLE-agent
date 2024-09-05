import questionary


def ask_question(question: str):
    """
    Ask a question to the user.
    """
    from mle.utils.system import print_in_box

    print_in_box(question, title="MLE Agent", color="purple")
    answer = questionary.text("Type your answer here:").ask()
    return f"Question: {question}\nAnswer: {answer}"


def ask_yes_no(question: str):
    """
    Ask a yes/no question to the user.
    """
    from mle.utils.system import print_in_box

    print_in_box(question, title="MLE Agent", color="purple")
    return questionary.confirm("Type your answer here:").ask()


def ask_choices(question: str, choices: list):
    """
    Ask a multiple choice question to the user.
    """
    from mle.utils.system import print_in_box

    print_in_box(question, title="MLE Agent", color="purple")
    return questionary.select("Type your answer here:", choices=choices).ask()
