#!/usr/bin/env python3
"""
Multi-Agent LLM System for Kaggle Problem Solving
Powered by OpenAI API using LangGraph with ReAct workflow
"""

import json
import os
import requests
import xml.etree.ElementTree as ElementTree
from typing import Dict, List, Any, TypedDict, Annotated
from dataclasses import dataclass
from enum import Enum

import openai
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    problem_description: str
    research_findings: str
    implementation_plan: str
    generated_code: str
    current_agent: str
    iteration_count: int
    target_root_dir: str


@dataclass
class FunctionCall:
    name: str
    arguments: Dict[str, Any]


class AgentType(Enum):
    ADVISOR = "advisor"
    PLANNER = "planner"
    DEVELOPER = "developer"


def setup_openai_api():
    """Setup OpenAI API key from environment or user input"""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("🔑 OpenAI API Key not found in environment variables.")
        api_key = input("Please enter your OpenAI API key: ").strip()

        if not api_key:
            raise ValueError("OpenAI API key is required to run the agent system")

        # Set the API key for the current session
        os.environ["OPENAI_API_KEY"] = api_key
        print("✅ API key set successfully\n")
    else:
        print("✅ Found OpenAI API key in environment\n")

    openai.api_key = api_key
    return api_key


def search_arxiv(query: str, max_results: int = 5) -> str:
    url = 'https://export.arxiv.org/api/query'
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f"Error: Unable to fetch data from arXiv (Status code: {response.status_code})"

    root = ElementTree.fromstring(response.content)
    output = ""
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
        link = entry.find('{http://www.w3.org/2005/Atom}id').text
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in
                   entry.findall('{http://www.w3.org/2005/Atom}author')]

        output += f"""
        Title: {title.strip()}
        Summary: {summary.strip()}
        Link: {link.strip()}
        Published: {published.strip()}
        Authors: {authors}
        """

    return output


def search_papers_with_code(query: str, max_results: int = 8) -> str:
    url = f"https://paperswithcode.com/api/v1/search/"
    response = requests.get(url, params={'page': 1, 'q': query})
    if response.status_code != 200:
        return "Failed to retrieve data from Papers With Code."

    data = response.json()
    if 'results' not in data:
        return "No results found for the given query."

    results = data['results'][:int(max_results)]  # Get top-k results
    result_strings = []

    for result in results:
        paper = result['paper']
        paper_title = paper.get('title', 'No title available')
        abstract = paper.get('abstract', 'No abstract available')
        paper_pdf_url = paper.get('url_pdf', 'No PDF available')
        repository = result.get('repository', [])
        if repository:
            code_url = repository.get('url', 'No official code link available')
        else:
            code_url = 'No official code link available'

        result_string = f"Title: {paper_title}\nAbstract:{abstract}\nPaper URL: {paper_pdf_url}\nCode URL: {code_url}\n"
        result_strings.append(result_string)

    return "\n".join(result_strings)


def write_file(filepath: str, content: str) -> bool:
    """
    Write content to a file.
    Args:
        filepath (str): The path to the file to write to.
        content (str): The content to write to the file.
    """
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        return f"Content written to file: {filepath}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"


def mkdir(directory: str) -> bool:
    """
    Create a directory if it does not exist.
    Args:
        path (str): The path to the directory to create.
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return f"Directory '{directory}' created successfully."
    except OSError as error:
        return f"Creation of the directory '{directory}' failed due to: {error}"


def read_file(file_path: str, limit: int = 2000):
    """
    Reads the contents of a file and returns it as a string.

    Args:
    file_path (str): The path to the file that needs to be read.
    limit (int, optional): Maximum number of lines to read.

    Returns:
    str: The contents of the file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            if limit <= 0:
                return file.read()
            lines = []
            for i, line in enumerate(file):
                if i >= limit:
                    break
                lines.append(line)
            return ''.join(lines)
    except FileNotFoundError:
        return f"File not found: {file_path}"


FUNCTION_SCHEMAS = {
    "search_arxiv": {
        "type": "function",
        "function": {
            "name": "search_arxiv",
            "description": "Search arXiv papers for research related to machine learning and data science",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for arXiv papers"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    "search_papers_with_code": {
        "type": "function",
        "function": {
            "name": "search_papers_with_code",
            "description": "Search Papers with Code for implementations and benchmarks",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for Papers with Code"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    "write_file": {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                },
                "required": ["filepath", "content"]
            }
        }
    },
    "mkdir": {
        "type": "function",
        "function": {
            "name": "mkdir",
            "description": "Create a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path to create"}
                },
                "required": ["directory"]
            }
        }
    },
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to read"},
                    "limit": {"type": "integer", "description": "Maximum number of lines to read", "default": 2000}
                },
                "required": ["file_path"]
            }
        }
    },
}

FUNCTION_MAP = {
    "search_arxiv": search_arxiv,
    "search_papers_with_code": search_papers_with_code,
    "write_file": write_file,
    "mkdir": mkdir,
    "read_file": read_file
}


def call_openai_with_tools(messages: List[Dict], available_tools: List[str], temperature: float = 0.7) -> Dict:
    """Call OpenAI API with function calling capability"""
    tools = [FUNCTION_SCHEMAS[tool] for tool in available_tools]

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools if tools else None,
        tool_choice="auto" if tools else None,
        temperature=temperature
    )

    return response


def execute_function_call(function_name: str, arguments: Dict) -> Any:
    """Execute a function call and return the result"""
    if function_name in FUNCTION_MAP:
        return FUNCTION_MAP[function_name](**arguments)
    else:
        raise ValueError(f"Unknown function: {function_name}")


class AdvisorAgent:
    def __init__(self):
        self.available_tools = ["search_arxiv", "search_papers_with_code"]

    def process(self, state: AgentState) -> AgentState:
        print("🔍 ADVISOR AGENT: Starting research phase...")
        problem = state["problem_description"]

        system_prompt = f"""You are an AI research advisor. Your job is to search for relevant research papers and implementations that could help solve the given Kaggle problem.

Problem: {problem}

Use the search_arxiv and search_papers_with_code functions to find relevant papers and implementations. Provide a summary of your findings including:
1. Key research papers that are relevant
2. State-of-the-art approaches
3. Available implementations and code

Be thorough but concise in your research."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please research solutions for this Kaggle problem: {problem}"}
        ]

        research_findings = ""
        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            print(f"  📊 Research iteration {iteration + 1}/{max_iterations}")
            response = call_openai_with_tools(messages, self.available_tools)
            message = response.choices[0].message

            if message.tool_calls:
                print(f"  🔧 Executing {len(message.tool_calls)} research tool(s)...")
                messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})

                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    print(f"    • Calling {function_name}")
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Raw arguments: {tool_call.function.arguments}")
                        # Try to clean the arguments
                        cleaned_args = tool_call.function.arguments.replace('\n', '\\n').replace('\r', '\\r').replace(
                            '\t', '\\t')
                        try:
                            arguments = json.loads(cleaned_args)
                        except:
                            # If still fails, provide default arguments
                            arguments = {"query": "machine learning", "max_results": 5}

                    result = execute_function_call(function_name, arguments)
                    print(f"    ✅ {function_name} completed")

                    messages.append({
                        "role": "tool",
                        "content": str(result) if not isinstance(result, str) else result,
                        "tool_call_id": tool_call.id
                    })
            else:
                research_findings = message.content
                print("  ✅ Research completed")
                break

            iteration += 1

        state["research_findings"] = research_findings
        state["current_agent"] = AgentType.PLANNER.value
        state["messages"].append(AIMessage(content=f"Research completed: {research_findings}"))
        print("🔍 ADVISOR AGENT: Research phase completed!\n")

        return state


class PlannerAgent:
    def process(self, state: AgentState) -> AgentState:
        print("📋 PLANNER AGENT: Creating implementation plan...")
        problem = state["problem_description"]
        research = state["research_findings"]

        system_prompt = f"""You are an AI planning agent. Based on the research findings, create a detailed implementation plan for solving the Kaggle problem.

Problem: {problem}
Research Findings: {research}

Create a step-by-step implementation plan that includes:
1. Data preprocessing steps
2. Model architecture recommendations
3. Training strategy
4. Evaluation metrics
5. Key code components needed

Be specific and actionable."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Create an implementation plan based on the research findings."}
        ]

        print("  🤖 Generating implementation plan...")
        response = call_openai_with_tools(messages, [])
        plan = response.choices[0].message.content
        print("  ✅ Implementation plan created")

        state["implementation_plan"] = plan
        state["current_agent"] = AgentType.DEVELOPER.value
        state["messages"].append(AIMessage(content=f"Implementation plan created: {plan}"))
        print("📋 PLANNER AGENT: Planning phase completed!\n")

        return state


class DeveloperAgent:
    def __init__(self):
        self.available_tools = ["write_file", "mkdir", "read_file"]

    def process(self, state: AgentState) -> AgentState:
        print("💻 DEVELOPER AGENT: Starting code generation...")
        problem = state["problem_description"]
        plan = state["implementation_plan"]
        target_dir = state["target_root_dir"]

        system_prompt = f"""You are an AI developer agent. Based on the implementation plan, generate Python code to solve the Kaggle problem.

Problem: {problem}
Implementation Plan: {plan}
Target Directory: {target_dir}

Generate complete, working Python code that implements the solution. Use the write_file, mkdir, and read_file functions to create the necessary files and code structure.

IMPORTANT: All files should be created within the target directory: {target_dir}
- Use mkdir to create the target directory structure first
- All file paths should be relative to or within {target_dir}

Focus on:
1. Clean, readable code
2. Proper data handling
3. Model implementation
4. Training and evaluation logic
5. Kaggle submission format

Create a complete solution with all necessary files in the specified directory."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the complete code implementation based on the plan."}
        ]

        generated_code = ""
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            print(f"  💾 Code generation iteration {iteration + 1}/{max_iterations}")
            response = call_openai_with_tools(messages, self.available_tools)
            message = response.choices[0].message

            if message.tool_calls:
                print(f"  🔧 Executing {len(message.tool_calls)} development tool(s)...")
                messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})

                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    print(f"    • Calling {function_name}")
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Raw arguments: {tool_call.function.arguments}")
                        # Try to clean the arguments
                        cleaned_args = tool_call.function.arguments.replace('\n', '\\n').replace('\r', '\\r').replace(
                            '\t', '\\t')
                        try:
                            arguments = json.loads(cleaned_args)
                        except:
                            # If still fails, provide default arguments
                            arguments = {"query": "machine learning", "max_results": 5}

                    result = execute_function_call(function_name, arguments)
                    print(f"    ✅ {function_name} completed")

                    messages.append({
                        "role": "tool",
                        "content": str(result) if not isinstance(result, str) else result,
                        "tool_call_id": tool_call.id
                    })
            else:
                generated_code = message.content
                print("  ✅ Code generation completed")
                break

            iteration += 1

        state["generated_code"] = generated_code
        state["current_agent"] = "completed"
        state["messages"].append(AIMessage(content=f"Code generation completed: {generated_code}"))
        print("💻 DEVELOPER AGENT: Code generation phase completed!\n")

        return state


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow"""
    workflow = StateGraph(AgentState)

    advisor = AdvisorAgent()
    planner = PlannerAgent()
    developer = DeveloperAgent()

    workflow.add_node("advisor", advisor.process)
    workflow.add_node("planner", planner.process)
    workflow.add_node("developer", developer.process)

    def route_next_agent(state: AgentState) -> str:
        current = state["current_agent"]
        if current == AgentType.PLANNER.value:
            return "planner"
        elif current == AgentType.DEVELOPER.value:
            return "developer"
        elif current == "completed":
            return END
        return END

    workflow.add_edge(START, "advisor")
    workflow.add_conditional_edges("advisor", route_next_agent)
    workflow.add_conditional_edges("planner", route_next_agent)
    workflow.add_conditional_edges("developer", route_next_agent)

    return workflow.compile()


def solve_kaggle_problem(problem_description: str, target_root_dir: str = "./kaggle_solution") -> Dict[str, Any]:
    """Main function to solve a Kaggle problem using the multi-agent system

    Args:
        problem_description: Description of the Kaggle problem to solve
        target_root_dir: Root directory where solution files will be created
    """

    print("🚀 KAGGLE AGENT SYSTEM: Starting problem solving workflow...")
    print(f"📝 Problem: {problem_description[:100]}...")
    print(f"📁 Target Directory: {target_root_dir}\n")

    initial_state = AgentState(
        messages=[HumanMessage(content=problem_description)],
        problem_description=problem_description,
        research_findings="",
        implementation_plan="",
        generated_code="",
        current_agent=AgentType.ADVISOR.value,
        iteration_count=0,
        target_root_dir=target_root_dir
    )

    workflow = create_workflow()
    print("⚡ Workflow created, starting execution...\n")
    result = workflow.invoke(initial_state)
    print("🎉 WORKFLOW COMPLETED SUCCESSFULLY!\n")

    return {
        "problem": result["problem_description"],
        "research": result["research_findings"],
        "plan": result["implementation_plan"],
        "code": result["generated_code"],
        "messages": [msg.content for msg in result["messages"]]
    }


if __name__ == "__main__":
    # Setup OpenAI API key first
    setup_openai_api()

    problem = """
    Kaggle Competition: Predict the MNIST Dataset
    Description: Build a model to classify handwritten digits from the MNIST dataset.
    Dataset: MNIST dataset containing images of handwritten digits (0-9)
    Goal: Achieve the highest accuracy on the test set.
    Evaluation: Accuracy score on the test set
    Submission Format: CSV file with two columns: 'ImageId' and 'Label'
    """

    # Allow user to specify target directory
    import sys

    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = input("Enter target directory for solution files (default: ./kaggle_solution): ").strip()
        if not target_dir:
            target_dir = "./kaggle_solution"

    print("Starting Kaggle Problem Solver...")
    print(f"Problem: {problem}")
    print(f"Target Directory: {target_dir}")
    print("\n" + "=" * 50 + "\n")

    result = solve_kaggle_problem(problem, target_dir)

    print("SOLUTION SUMMARY:")
    print(f"Research Findings: {result['research']}")
    print(f"Implementation Plan: {result['plan']}")
    print(f"Generated Code: {result['code']}")
    print(f"Files created in: {target_dir}")
