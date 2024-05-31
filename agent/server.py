"""
The RESTFul server of MLE-Agent
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from agent.utils import *
from agent.function import Chat
from agent.types import Project, ConfigUpdateRequest

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


@app.put("/config/update")
def update_config(request: ConfigUpdateRequest):
    try:
        config.write_section(request.section_name, request.config_dict, request.overwrite)
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects/", response_model=Project)
def create_project(project: Project):
    create_project(project)
    return project


@app.get("/project/")
def list_project():
    """
    List all the projects.
    :return: the list of projects.
    """
    return {'projects': [p.dict() for p in list_projects()]}


@app.get("/project/{project_name}", response_model=Project)
def get_project(project_name: str):
    result = read_project_state(project_name)
    if result:
        return result
    else:
        raise HTTPException(status_code=404, detail="Project not found")


# run
@app.get("/run/")
def run_project():
    """
    run_project: Run the project.
    :return: the run status.
    """
    return {"status": "Running"}


@app.get("/chat/")
def chat(project: str, message: str):
    """
    Call the Chat's api function and return the streaming response. The input is an object with the project.
    """
    project_state = read_project_state(project)
    user_pmpt = message

    chat_app = Chat(load_model())
    chat_app.add(role='system', content=pmpt_chat_init(project_state))
    local_files_info = list_all_files(project_state.path)
    chat_app.add("user", f"""The files under the project directory is: {local_files_info}""")

    def generate_response(p):
        previous_text = ''
        for text in chat_app.handle_response(p):
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
