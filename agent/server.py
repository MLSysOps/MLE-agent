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
    return {"message": "Hello World"}


@app.post("/items/")
def create_item(name: str):
    return {"name": name, "status": "Item created"}


def start_server(address: str = '0.0.0.0', port: int = 8080):
    """
    Start the server.
    :param address: the server address.
    :param port: the server port.
    :return: None
    """
    uvicorn.run(app, host=address, port=port)
