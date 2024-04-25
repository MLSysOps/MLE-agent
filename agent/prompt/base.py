from agent.types import Step

from agent.templates import load_step


def pmpt_sys_init(
        lang: str
) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working on
     an ML project using {lang} as the primary language.
    
    You are asked to generate a code script and the corresponding file name based on the user requirements.
    The output format should be:
    
    File Name: {{file name}}
    
    Code: {{code}}
    
    """


def hint_step(
        step: Step
) -> str:
    return f"""
    You are currently working on step {step} of the project.
    An ML project in our workflow contains multiple steps, and each step is a task that you need to complete.
    
    Now, you are currently on step {step.step}:{step.name}
    This step is about {step.description}
    
    """


if __name__ == "__main__":
    print(hint_step(load_step("data_collection.yml")))
