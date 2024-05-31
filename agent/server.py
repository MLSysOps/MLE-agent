"""
The RESTful server of MLE-Agent
"""
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from agent.utils import Config
from agent.function import Chat
from agent.utils.prompt import pmpt_chat_init
from agent.utils import load_model, read_project_state, list_all_files

app = FastAPI()
origins = ["*"]
config = Config()

# handle the CROSS origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to MLE-Agent!"}


@app.post("/config/")
def config():
    """
    Configure the MLE-Agent.
    :return: the configuration data.
    """
    return {"status": "Configured"}


@app.post("/project/")
def create_project():
    """
    Create a new project.
    :return: the data of the new project.
    """
    return {"status": "Project created"}


@app.get("/project/{project_id}")
def get_project(project_id: int):
    return {"project_id": project_id}


# run
@app.get("/run/")
def run_project():
    """
    run_project: Run the project.
    :return: the run status.
    """
    return {"status": "Running"}


@app.get("/chat/")
async def chat(project: str, message: str):
    """
    Call the Chat's api function and return the streaming response. The input is an object with the project.
    """
    project_state = read_project_state(project)
    user_pmpt = message

    chat_app = Chat(load_model())
    chat_app.add(role='system', content=pmpt_chat_init(project_state))
    local_files_info = list_all_files(project_state.path)
    chat_app.add("user", f"""The files under the project directory is: {local_files_info}""")

    async def generate_response(prompt):
        previous_text = ''
        for text in chat_app.handle_response(prompt):
            new_text = text[len(previous_text):]
            previous_text = text
            yield new_text

    return StreamingResponse(generate_response(user_pmpt), media_type="text/event-stream")


def start_server(address: str = "0.0.0.0", port: int = 8080):
    """
    Start the server.
    :param address: the server address.
    :param port: the server port.
    :return: None
    """
    uvicorn.run(app, host=address, port=port)
