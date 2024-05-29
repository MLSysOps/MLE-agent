from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class DebugEnv(str, Enum):
    local = "local"
    cloud = "cloud"


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
    current_task: int
    dataset: Optional[str] = None
    data_kind: Optional[str] = None
    ml_task_type: Optional[str] = None
    ml_model_arch: Optional[str] = None
    tasks: Optional[List[Task]] = None


class Project(BaseModel):
    name: str
    path: str
    lang: str
    llm: str
    plan: Optional[Plan] = None
    entry_file: Optional[str] = None
    debug_env: Optional[str] = DebugEnv.local
    description: Optional[str] = None
    requirement: Optional[str] = None