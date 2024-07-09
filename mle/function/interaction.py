import questionary


def ask_question(question: str):
    """
    Ask a question to the user.
    """
    answer = input("[ADVISOR]: " + question)
    return f"Question: {question}\nAnswer: {answer}"


def ask_yes_no(question: str):
    """
    Ask a yes/no question to the user.
    """
    return questionary.confirm("[ADVISOR]: " + question).ask()


def ask_choices(question: str, choices: list):
    """
    Ask a multiple choice question to the user.
    """
    return "More details: " + questionary.select("[ADVISOR]: " + question, choices=choices).ask()
