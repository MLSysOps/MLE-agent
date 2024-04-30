from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI

from cfg import load_config


@chain
def model_selection_agent(input: str, llm: BaseChatModel):
    """
    Analyze the user's current ML development stage based on their input description.

    Args:
        input (str): The user's input describing their current work.
        llm (BaseChatModel): The language model used for processing the input.

    Returns:
        MLDevelopmentStage: Enum representing the identified ML development stage.
    """
    output_parser = StrOutputParser()
    prompt = PromptTemplate(
        template="""

        System: You play as a professional machine learning engineer. You are currently in the model training stage.
        You need to select and load a model for users to build a baseline given users query.

        Your output should be purely python code that can be run to load the model from appropriate library. 
        
        The user's input description is: {query}
        
        The python code generated is:
        
        """,
        input_variables=["query"]
    )

    chain = prompt | llm | output_parser
    return chain.invoke({"query": input})


if __name__ == "__main__":
    config = load_config('open_ai_key.json')

    OPENAI_API_KEY = config["OPENAI_API_KEY"]

    llm = ChatOpenAI(api_key=OPENAI_API_KEY)

    prompt = ("I want to use some lightweight model to build a sentiment analysis baseline on my dataset."
              "make sure you only import necessary packages"
              "make sure you also load the corresponding preprocessor like tokenizer and model.")

    model_selection_code = model_selection_agent.invoke(
        input=prompt,
        llm=llm  # Assuming 'llm' is your instantiated language model
    )

    with open("imdb_project/model_selection_GENERATED.py", "w") as py_file:
        py_file.write(model_selection_code)

    print(model_selection_code)
