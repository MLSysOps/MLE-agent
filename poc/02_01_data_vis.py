from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI

from cfg import load_config


@chain
def vis_agent(input: str, llm: BaseChatModel):
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
        
        System: You play as a professional data scientist. You are currently in the Data Engineering stage. You can read data 
        and then use tools like pandas, numpy, and matplotlib to visualize the data. 
        
        The first line of input is a file name with a path. 
        
        First, you should write code to read the data from {input_file_path} base on its suffix using proper tools like pandas, 
        etc.
        
        The second line of input is the header of the data you want to visualize.
        
        Second, based on the {sample_data}, you should write code to visualize the data using matplotlib, seaborn, or any other.
        
        The code must be tailored to the user's input and the text in the figure must be too.
        
        Your output should be purely python code that can be run to visualize the data. Please do not include 
        ```in front 
        of and after the code block.
        
        input: {input_file_path} \n {sample_data}
        
        Answer as a python code block:
        """,
        input_variables=["input_file_path", "sample_data"]
    )

    chain = prompt | llm | output_parser
    return chain.invoke({"input_file_path": input.split("\n")[0], "data_header": input.split("\n")[1:]})


if __name__ == "__main__":
    config = load_config('../credential.json')

    OPENAI_API_KEY = config["OPENAI_API_KEY"]

    llm = ChatOpenAI(api_key=OPENAI_API_KEY)

    prompt = ("output.csv \n text, label")

    vis_code = vis_agent.invoke(
        input=prompt,
        llm=llm  # Assuming 'llm' is your instantiated language model
    )

    with open("data_vis_GENERATED.py", "w") as py_file:
        py_file.write(vis_code)

    print(vis_code)