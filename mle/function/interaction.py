import questionary


def ask_question(question: str):
    """
    Ask a question to the user.
    """
    return questionary.text("[PLAN AGENT]: " + question).ask()


def ask_yes_no(question: str):
    """
    Ask a yes/no question to the user.
    """
    return questionary.confirm("[PLAN AGENT]: " + question).ask()


def ask_choices(question: str, choices: list):
    """
    Ask a multiple choice question to the user.
    """
    return questionary.select("[PLAN AGENT]: " + question, choices=choices).ask()
