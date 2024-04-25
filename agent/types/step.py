from pydantic import BaseModel


class Step(BaseModel):
    step: int
    name: str
    description: str
