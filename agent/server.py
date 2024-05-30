"""
The RESTful server of MLE-Agent
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from agent.utils import Config
from agent.function import Chat
from agent.types import ChatRequest
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


@app.post("/chat/")
async def chat(request: Request):
    """
    Call the Chat's api function and return the streaming response. The input is an object with the project.
    """
    data = await request.json()
    project = read_project_state(data.get("project"))
    user_pmpt = data.get("message")

    chat_app = Chat(load_model())
    chat_app.add(role='system', content=pmpt_chat_init(project))
    local_files_info = list_all_files(project.path)
    chat_app.add("user", f"""The files under the project directory is: {local_files_info}""")

    def generate_response(prompt):
        for text in chat_app.api(prompt):
            yield text

    return StreamingResponse(generate_response(user_pmpt), media_type="text/plain")


def start_server(address: str = "0.0.0.0", port: int = 8080):
    """
    Start the server.
    :param address: the server address.
    :param port: the server port.
    :return: None
    """
    uvicorn.run(app, host=address, port=port)
