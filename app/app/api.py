from .schemas import UserCreate, TaskUpdate, TaskCreate
from .db import DataBase
from .auth import verify_password, create_access_token, create_refresh_token
from .cache import Cache
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException, status


app = FastAPI()


@app.post('/auth/register')
async def registration(user: UserCreate):
	async with DataBase() as db:
		await db.create_user(user)
	return {'message': 'registration was successful'}


@app.post('/auth/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
	async with DataBase() as db:
		user = await db.get_user(form_data.username)
		if not user or not await verify_password(form_data.password, user.password_hash):
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username or password')
		access_token = await create_access_token(data={'sub': user.username})
		refresh_token = await create_refresh_token(data={'sub': user.username})
	return_value = {'message': 'login was successful', 'access-token': access_token, 'refresh-token': refresh_token}
	return return_value


@app.post('/auth/refresh')
async def refresh(refresh_token: str):
	async with Cache() as cache:
		username = await cache.check_recording(refresh_token)
		if username is None:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")
	access_token = await create_access_token(data={'sub': username})
	return_value = {'access-token': access_token}
	return return_value


@app.post('/tasks')
async def create_task(task: TaskCreate):
	async with DataBase() as db:
		await db.create_task(task)
	return_value = {'message': 'task create successful', 'task': f'{task.task_name}, {task.description}, {task.status}'}
	return return_value


@app.get('/tasks')
async def read_tasks(filter=None):
	async with DataBase() as db:
		return_value = await db.read_tasks(filter)
	return return_value


@app.put('/task/{id}')
async def update_task(id: int, task: TaskUpdate):
	async with DataBase() as db:
		await db.update_task(task, id)
	return_value = {'message': 'update task successful', 'task': f'{task.task_name}, {task.description}, {task.status}'}
	return return_value


@app.delete('/task/{id}')
async def delete_task(id: int):
	async with DataBase() as db:
		await db.delete_task(id)
	return {'message': 'delete task successful'}
