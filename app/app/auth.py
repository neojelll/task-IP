from jose import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from .cache import Cache
from datetime import datetime, timedelta
import secrets


SECRET_KEY = secrets.token_urlsafe(32)  
ALGORITHM = "HS256"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


async def verify_password(password, hash_password):
	return pwd_context.verify(password, hash_password)


async def get_password_hash(password):
	return pwd_context.hash(password)


async def create_access_token(data: dict):
	to_encode = data.copy()
	expire = datetime.now() + timedelta(minutes=30)
	to_encode.update({'exp': expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt


async def create_refresh_token(data: dict):
	to_encode = data.copy()
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	async with Cache() as cache:
		await cache.create_recording(to_encode.get('sub'), encoded_jwt)
	return encoded_jwt
