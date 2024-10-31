from sqlalchemy.ext.asyncio import (
	create_async_engine,
	AsyncSession,
	async_sessionmaker,
)
from sqlalchemy import select
from .auth import get_password_hash
from .schemas import UserCreate, TaskCreate, TaskUpdate
from .models import User, Task
from .logger import configure_logger
from loguru import logger
import os


configure_logger()


class DataBase:
	def __init__(self):
		database_url = f'postgresql+asyncpg://{os.environ["DB_USERNAME"]}:{os.environ["DB_PASSWORD"]}@{os.environ["DB_HOST"]}:{os.environ["DB_PORT"]}/{os.environ["DB_NAME"]}'
		self.async_engine = create_async_engine(database_url, echo=True, future=True)
		self.async_session = async_sessionmaker(bind=self.async_engine, class_=AsyncSession, expire_on_commit=False)

	async def __aenter__(self):
		self.session = self.async_session()
		return self
	
	async def create_user(self, user: UserCreate):
		new_user = User(username=user.username, password_hash=await get_password_hash(user.password))
		self.session.add(new_user)
		await self.session.commit()

	async def get_user(self, username: str):
		result = await self.session.execute(select(User).where(User.username == username))
		return result.scalars().first()
	
	async def create_task(self, task: TaskCreate):
		new_task = Task(task_name=task.task_name, description=task.description, status=task.status)
		self.session.add(new_task)
		await self.session.commit()

	async def read_tasks(self, filter):
		result = await self.session.execute(select(Task))
		return result.scalars().all()
	

	async def update_task(self, task: TaskUpdate, task_id: int):
		db_task = await self.session.get(Task, task_id)
		for key, value in task.model_dump().items():
			setattr(db_task, key, value)
		await self.session.commit()

	async def delete_task(self, task_id: int):
		db_task = await self.session.get(Task, task_id)
		await self.session.delete(db_task)
		await self.session.commit()
	
	async def __aexit__(self, exc_type, exc_value, traceback):
		await self.session.aclose()
