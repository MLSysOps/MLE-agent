"""
The service of MLE-Agent
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
