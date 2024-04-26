from pydantic import BaseModel


class ProjectState(BaseModel):
    name: str
    description: str
    step: int
    path: str
    llm: str
    lang: str
