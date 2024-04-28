from pydantic import BaseModel
from typing import Optional


class ProjectState(BaseModel):
    name: str
    description: Optional[str] = None
    step: int
    task: int
    path: str
    llm: str
    lang: str
