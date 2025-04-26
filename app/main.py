import uuid
import time
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE
from starlette.types import Message

from .config import settings, get_settings, Settings
from .models.input import ParseRequest, ParseURLRequest
from .models.output import ParseResponse, HealthResponse
from .services.parser import HTMLParserService
# from .services.webhook import WebhookService  # Commented out webhook integration
# from .services.airtable import AirtableService  # Commented out Airtable integration


app: FastAPI = Depends(lambda: __import__("app").app)

# Apply CORS middleware when app starts
_app = app if isinstance(app, FastAPI) else __import__("app").app

_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def request_body_limiter(request: Request, call_next):
    """Limit request body size to MAX_CONTENT_SIZE from settings."""
    original_receive = request._receive

    async def limited_receive() -> Message:
        message = await original_receive()
        if message["type"] == "http.request":
            body = message.get("body", b"")
            if len(body) > settings.MAX_CONTENT_SIZE:
                raise HTTPException(status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload too large")
        return message

    request._receive = limited_receive
    return await call_next(request)


_auto_parser = HTMLParserService()
# webhook = WebhookService()  # Commented out webhook service
# airtable = AirtableService()  # Commented out Airtable service


@_app.post("/api/v1/parse", response_model=ParseResponse, status_code=status.HTTP_200_OK)
async def parse_html(
    payload: ParseRequest,
    background_tasks: BackgroundTasks,
    app_settings: Annotated[Settings, Depends(get_settings)] = settings,
):
    """Parse raw HTML into markdown and extract metadata."""

    start_time = time.perf_counter()

    markdown_content, metadata = _auto_parser.parse(payload.html, payload.source_url)

    end_time = time.perf_counter()
    elapsed_ms = int((end_time - start_time) * 1000)

    response = ParseResponse(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        source_url=payload.source_url,
        status="success",
        markdown=markdown_content,
        metadata=metadata,
        processing_time_ms=elapsed_ms,
        record_id=payload.record_id,
    )

    # Sync with Airtable asynchronously (if configured)
    # if airtable.is_configured():
    #     background_tasks.add_task(airtable.sync_parsed_content, response)

    # Trigger webhook asynchronously (if configured)
    # if app_settings.WEBHOOK_URL:
    #     background_tasks.add_task(webhook.deliver, response)

    return response


@_app.post("/api/v1/parse-url", response_model=ParseResponse, status_code=status.HTTP_200_OK)
async def parse_url(
    payload: ParseURLRequest,
    background_tasks: BackgroundTasks,
    app_settings: Annotated[Settings, Depends(get_settings)] = settings,
):
    """Fetch URL content then parse HTML."""
    start_time = time.perf_counter()

    try:
        html_content = _auto_parser.fetch(payload.url)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {exc}") from exc

    markdown_content, metadata = _auto_parser.parse(html_content, payload.url)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    response = ParseResponse(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        source_url=payload.url,
        status="success",
        markdown=markdown_content,
        metadata=metadata,
        processing_time_ms=elapsed_ms,
        record_id=payload.record_id,
    )

    # Sync with Airtable asynchronously (if configured)
    # if airtable.is_configured():
    #     background_tasks.add_task(airtable.sync_parsed_content, response)

    # Trigger webhook asynchronously (if configured)
    # if app_settings.WEBHOOK_URL:
    #     background_tasks.add_task(webhook.deliver, response)

    return response


@_app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Simple health check."""
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))


# Global exception handlers


@_app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # noqa: D401
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@_app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # noqa: D401
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# Register body limiter middleware
_app.middleware("http")(request_body_limiter) 