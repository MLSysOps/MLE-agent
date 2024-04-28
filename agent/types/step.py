from pydantic import BaseModel
from typing import List, Optional


class Resource(BaseModel):
    name: str
    description: str
    choice: Optional[List[str]] = None


class Function(BaseModel):
    name: str
    description: str


class Task(BaseModel):
    name: str
    description: str
    resources: Optional[List[Resource]] = None
    functions: Optional[List[str]] = None


class Step(BaseModel):
    step: int
    name: str
    description: str
    tasks: Optional[List[Task]] = None
