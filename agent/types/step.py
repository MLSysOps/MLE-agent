from pydantic import BaseModel
from typing import List, Optional


class Resource(BaseModel):
    name: str
    description: Optional[str] = None
    choice: Optional[List[str]] = None


class Function(BaseModel):
    name: str
    description: Optional[str] = None


class Task(BaseModel):
    name: str
    kind: str
    description: Optional[str] = None
    resources: Optional[List[Resource]] = None
    functions: Optional[List[str]] = None


class Step(BaseModel):
    step: int
    name: str
    description: Optional[str] = None
    tasks: Optional[List[Task]] = None
