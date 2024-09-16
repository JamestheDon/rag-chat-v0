from pydantic import BaseModel

class Message(BaseModel):
    content: str

class Response(BaseModel):
    content: str