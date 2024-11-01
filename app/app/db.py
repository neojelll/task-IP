from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import select, func
from .auth import get_password_hash
from .schemas import UserCreate, TaskCreate, TaskUpdate
from .models import User, Task
from .logger import configure_logger
from loguru import logger
from fastapi import HTTPException, status
import os
import re


configure_logger()


class DataBase:
    def __init__(self):
        database_url = f'postgresql+asyncpg://{os.environ["DB_USERNAME"]}:{os.environ["DB_PASSWORD"]}@{os.environ["DB_HOST"]}:{os.environ["DB_PORT"]}/{os.environ["DB_NAME"]}'
        self.async_engine = create_async_engine(database_url, echo=True, future=True)
        self.async_session = async_sessionmaker(
            bind=self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def __aenter__(self):
        self.session = self.async_session()
        return self

    async def create_user(self, user: UserCreate):
        try:
            new_user = User(
                username=user.username,
                password_hash=await get_password_hash(user.password),
            )
            self.session.add(new_user)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error when created user: {e}")

    async def get_user(self, username: str):
        try:
            result = await self.session.execute(
                select(User).where(User.username == username)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error when get user: {e}")
            return None

    async def create_task(self, task: TaskCreate, user_id):
        try:
            new_task = Task(
                task_name=task.task_name,
                description=task.description,
                status=task.status,
                user_id=user_id,
            )
            self.session.add(new_task)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error when created task: {e}")

    async def read_tasks(self, user_id, filter):
        try:
            if filter is None:
                result = await self.session.execute(
                    select(Task).where(Task.user_id == user_id)
                )
                return result.scalars().all()

            pattern = re.escape(filter.lower())
            result = await self.session.execute(
                select(Task).where(
                    func.lower(Task.status).regexp(pattern) & (Task.user_id == user_id)
                )
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error when read task: {e}")

    async def update_task(self, task: TaskUpdate, task_id: int, user_id):
        try:
            db_task = await self.session.get(Task, task_id)

            if db_task is None:
                logger.error(f"Task with id {task_id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Task not found."
                )

            if db_task.user_id != user_id:
                logger.error(
                    f"User  {user_id} is not authorized to update task {task_id}."
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unauthorized to update this task.",
                )

            for key, value in task.model_dump().items():
                setattr(db_task, key, value)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error when updated task: {e}")

    async def delete_task(self, task_id: int, user_id):
        try:
            db_task = await self.session.get(Task, task_id)

            if db_task is None:
                logger.error(f"Task with id {task_id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Task not found."
                )

            if db_task.user_id != user_id:
                logger.error(
                    f"User  {user_id} is not authorized to delete task {task_id}."
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unauthorized to delete this task.",
                )

            await self.session.delete(db_task)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error when deleted task: {e}")

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.session.aclose()
