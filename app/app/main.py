from .api import app
import uvicorn


def run() -> None:
	uvicorn.run(app, host='0.0.0.0', port=8000)
