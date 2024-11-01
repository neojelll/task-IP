from .schemas import UserCreate, TaskUpdate, TaskCreate
from .db import DataBase
from .auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from .cache import Cache
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException, status, Header, Query
from jose import JWTError
from .logger import configure_logger
from loguru import logger


configure_logger()


async def verify_token(authorization):
    try:
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorization header missing or invalid",
            )
        token = authorization.split(" ")[1]
        payload = await decode_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        )


app = FastAPI()


@app.post("/auth/register")
async def registration(user: UserCreate):
    logger.debug(f"Start registration, params: {user}")
    async with DataBase() as db:
        await db.create_user(user)
    logger.debug("Registration was successful")
    return {"message": "registration was successful"}


@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.debug(f"Start login, params: {form_data}")
    async with DataBase() as db:
        user = await db.get_user(form_data.username)
        if not user or not await verify_password(
            form_data.password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or password",
            )
        access_token = await create_access_token(data={"sub": user.username})
        refresh_token = await create_refresh_token(data={"sub": user.username})
    return_value = {
        "message": "login was successful",
        "access-token": access_token,
        "refresh-token": refresh_token,
    }
    logger.debug(f"Loging was successful, return_value: {return_value}")
    return return_value


@app.post("/auth/refresh")
async def refresh(refresh_token: str):
    logger.debug(f"Start refresh, params: {refresh_token}")
    async with Cache() as cache:
        username = await cache.check_recording(refresh_token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
    access_token = await create_access_token(data={"sub": username})
    return_value = {"access-token": access_token}
    logger.debug(f"refresh was successful, return_value: {return_value}")
    return return_value


@app.post("/tasks")
async def create_task(task: TaskCreate, authorization: str = Header(None)):
    logger.debug(f"Start create_task, params: {task, authorization}")
    username = await verify_token(authorization)
    async with DataBase() as db:
        user = await db.get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="user not founded in db",
            )
        await db.create_task(task, user.id)
    return_value = {
        "message": "task create successful",
        "task": f"{task.task_name}, {task.description}, {task.status}",
    }
    logger.debug(f"create_task was successful, return_value: {return_value}")
    return return_value


@app.get("/tasks")
async def read_tasks(
    authorization: str = Header(None), filter_status: str = Query(None)
):
    logger.debug(f"Start read_task, params: {authorization, filter_status}")
    username = await verify_token(authorization)
    async with DataBase() as db:
        user = await db.get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="user not founded in db"
            )
        return_value = await db.read_tasks(user.id, filter_status)
    logger.debug(f"read_task was successful, return_value: {return_value}")
    return return_value


@app.put("/task/{id}")
async def update_task(id: int, task: TaskUpdate, authorization: str = Header(None)):
    logger.debug(f"Start update_task, params: {id, task, authorization}")
    username = await verify_token(authorization)
    async with DataBase() as db:
        user = await db.get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="user not founded in db"
            )
        await db.update_task(task, id, user.id)
    return_value = {
        "message": "update task successful",
        "task": f"{task.task_name}, {task.description}, {task.status}",
    }
    logger.debug(f"update_task was successful, return_value: {return_value}")
    return return_value


@app.delete("/task/{id}")
async def delete_task(id: int, authorization: str = Header(None)):
    logger.debug(f"Start delete_task, params {id, authorization}")
    username = await verify_token(authorization)
    async with DataBase() as db:
        user = await db.get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="user not founded in db"
            )
        await db.delete_task(id, user.id)
    logger.debug("delete_task was successful")
    return {"message": "delete task successful"}
