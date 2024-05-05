from agent.types import Step


def pmpt_sys_init(
        lang: str,
        step: Step
) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working on an ML project using {lang} as the primary language. The ML project contains multiple steps, and each step is a task that you need to complete by generating a code script and the corresponding file name based on the user requirements.
    
    Now, you are currently on step {step.step}:{step.name}
    The output format should be:
    
    File Name: {{name}}
    
    Code: {{code}}
    
    """


def pmpt_chain_init(lang: str) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working on an
     ML project using {lang} as the primary language.
    Please generate a code script for the current task based on following information.

    Output format should be:

    Code: {{code}}
    """


def pmpt_chain_code(lang: str, code: str) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working on an ML project using
     {lang} as the primary language.
    Please modify (or add new features to) the following code to meet the task requirements.

    Existing Code: {code}

    The output format should be:

    Code: {{code}}
    """


def pmpt_chain_filename(lang: str) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working
     on an ML project using {lang} as the primary language.
    Now are are given a user requirement to generate a file name for the current task,
     note the file suffix (e.g., .py) should be correct.

    Output format should be:

    File Name: {{name}}

    """


def pmpt_ml_project():
    return f"""
    
    """
