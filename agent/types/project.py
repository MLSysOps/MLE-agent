from pydantic import BaseModel


class ProjectState(BaseModel):
    name: str
    description: str
    state: str
    path: str
