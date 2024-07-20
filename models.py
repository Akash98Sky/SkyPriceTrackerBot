from pydantic import BaseModel

class ActionEvent(BaseModel):
    id: str
    trigger: str

class ActionBody(BaseModel):
    event: ActionEvent