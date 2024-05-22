from pydantic import BaseModel
from typing import List, Optional


class Resource(BaseModel):
    name: str
    uri: Optional[str] = None
    description: Optional[str] = None
    choices: Optional[List[str]] = None


class Function(BaseModel):
    name: str
    description: Optional[str] = None


class Task(BaseModel):
    name: str
    kind: str
    description: Optional[str] = None
    resources: Optional[List[Resource]] = None
    functions: Optional[List[str]] = None
    debug: Optional[int] = None


class Plan(BaseModel):
    project_name: str
    project: str
    current_task: int
    lang: str
    llm: str
    training_entry_file: Optional[str] = None
    debug_env: Optional[str] = None
    requirement: Optional[str] = None
    dataset: Optional[str] = None
    tasks: Optional[List[Task]] = None
    description: Optional[str] = None
