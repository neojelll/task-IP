from redis.asyncio import Redis
from .logger import configure_logger
from loguru import logger
import os


configure_logger()


class Cache:
    def __init__(self):
        self.session = Redis(
            host=os.environ["CACHE_HOST"],
            port=int(os.environ["CACHE_PORT"]),
            decode_responses=True,
        )

    async def __aenter__(self):
        return self

    async def create_recording(self, username, refresh_token: str):
        try:
            await self.session.set(refresh_token, username, ex=3600 * 24 * 7)
        except Exception as e:
            logger.error(f"Error when set in cache: {e}")

    async def check_recording(self, refresh_token):
        try:
            return await self.session.get(refresh_token)
        except Exception as e:
            logger.error(f"Error when get in cache: {e}")

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.session.aclose()
