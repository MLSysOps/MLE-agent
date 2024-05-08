from pydantic import BaseModel
from typing import Optional


class ProjectState(BaseModel):
    name: str
    step: int
    task: int
    path: str
    llm: str
    lang: str
    description: Optional[str] = None
    target_file: Optional[str] = None
    user_requirement: Optional[str] = None
