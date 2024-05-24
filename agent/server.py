"""
The RESTful server of MLE-Agent
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["*"]

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


def start_server(address: str = '0.0.0.0', port: int = 8080):
    """
    Start the server.
    :param address: the server address.
    :param port: the server port.
    :return: None
    """
    uvicorn.run(app, host=address, port=port)
