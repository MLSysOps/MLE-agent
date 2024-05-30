from pydantic import BaseModel


class ChatRequest(BaseModel):
    """
    ChatRequest: the request model for chat.
    """
    project: str
    message: str
