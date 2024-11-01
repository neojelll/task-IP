from pydantic import BaseModel


class TaskCreate(BaseModel):
    task_name: str
    description: str
    status: str


class TaskUpdate(BaseModel):
    task_name: str
    description: str
    status: str


class UserCreate(BaseModel):
    username: str
    password: str
