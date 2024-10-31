from pydantic import BaseModel, constr
from typing import Optional


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
