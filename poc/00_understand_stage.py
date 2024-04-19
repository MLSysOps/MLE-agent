from langchain_openai import ChatOpenAI


from enum import Enum
from langchain.output_parsers import EnumOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import chain

# Define an Enum for ML Development Stages
class MLDevelopmentStage(Enum):
    PROBLEM_DEFINITION = "Problem Definition"
    DATA_COLLECTION = "Data Collection"
    DATA_ENGINEERING = "Data Engineering"
    MODEL_TRAINING = "Model Training"
    MODEL_EVALUATION = "Model Evaluation"
    MODEL_DEPLOYMENT = "Model Deployment"

@chain
def analyze_ml_development_stage(input: str, llm: BaseChatModel) -> MLDevelopmentStage:
    """
    Analyze the user's current ML development stage based on their input description.

    Args:
        input (str): The user's input describing their current work.
        llm (BaseChatModel): The language model used for processing the input.

    Returns:
        MLDevelopmentStage: Enum representing the identified ML development stage.
    """
    parser = EnumOutputParser(enum=MLDevelopmentStage)
    prompt = PromptTemplate(
        template="""
        Welcome to the ML development stage analysis tool. We cover various stages like:
        - Problem Definition
        - Data Collection
        - Data Engineering
        - Model Training
        - Model Evaluation
        - Model Deployment

        Please provide some information about what you are currently working on in your ML project,
        and I will help identify the stage you are likely at.

        The user's input description is: {input}
        Identified ML development stage is:
        """,
        input_variables=["input"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser
    return chain.invoke({"input": input})


if __name__ == "__main__":
    # Example usage:
    llm = ChatOpenAI(api_key="OpenAI_API_KEY")
    # Example corrected usage:
    stage_result = analyze_ml_development_stage.invoke(
        input="I am currently selecting features and cleaning data",
        llm=llm  # Assuming 'llm' is your instantiated language model
    )

    # To access the result:
    print("You are likely at the:", stage_result.name)
