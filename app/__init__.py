from fastapi import FastAPI
import logging

from logging import StreamHandler

from .config import settings

# Configure root logging format and level early
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[StreamHandler()],
)

app = FastAPI(
    title="Scientific HTML Parser API",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
)

# Import routes to register them with the FastAPI instance
from . import main  # noqa: E402  # pylint: disable=wrong-import-position 