import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI

from cfg import load_config

def read_python_files_into_dict(directory):
    """Reads all Python files in the given directory into a dictionary.

    Args:
        directory (str): The directory containing the Python files.

    Returns:
        dict: A dictionary mapping filenames to their code.
    """
    python_files = [f for f in os.listdir(directory) if f.endswith('.py')]
    code_dict = {}
    for file in python_files:
        file_path = os.path.join(directory, file)
        with open(file_path, 'r') as f:
            code_dict[file] = f.read()
    return code_dict



@chain
def model_training_agent(input: str, llm: BaseChatModel):
    system_prompt = f"""you are an ML engineer in the model training stage.
    
    you need to first understand the exiting code already generated for the project.
    
    then you need to write model training code by importing the useful code from the existing code.
    
    remember to use some experiment tool like wandb or mlflow to track the experiment.
    
    Given the user input, return training code so users can directly copy it to a file and run it.
    
    returned codes should have no ``` in the front and end of the code block."""

    output_parser = StrOutputParser()

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{input}")]
    )

    chain = prompt | llm | output_parser
    return chain.invoke({"input": input})


if __name__ == "__main__":
    config = load_config('open_ai_key.json')

    OPENAI_API_KEY = config["OPENAI_API_KEY"]

    llm = ChatOpenAI(api_key=OPENAI_API_KEY)
    project_directory = "imdb_project"  # Adjust this to your project directory path
    code_dict = read_python_files_into_dict(project_directory)

    # Printing the dictionary for demonstration purposes
    for filename, code in code_dict.items():
        print(f"{filename}:\n{code}\n{'-' * 80}\n")

    prompt = (code_dict)

    model_training_code = (model_training_agent.invoke(
        input=prompt,
        llm=llm  # Assuming 'llm' is your instantiated language model
    ))

    with open("imdb_project/model_training_GENERATED.py", "w") as py_file:
        py_file.write(model_training_code)

    print(model_training_code)
