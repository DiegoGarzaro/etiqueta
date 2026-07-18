"""FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import async_session_factory, init_db
from app.services.auth import SESSION_COOKIE, auth_state, load_auth_state, verify_session_token
from app.services.errors import ServiceError

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables and load the auth configuration on startup.

    Args:
        app (FastAPI): The application instance.

    Yields:
        None: Control back to the running application.
    """
    await init_db()
    async with async_session_factory() as session:
        await load_auth_state(session)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_PUBLIC_API_PATHS = {"/api/auth/login", "/api/auth/status", "/api/auth/logout"}


@app.middleware("http")
async def enforce_pin(request: Request, call_next):  # noqa: ANN001, ANN201
    """Require a valid session cookie on API and media requests.

    Enforcement is skipped entirely while no PIN is configured. The login,
    status, and logout endpoints stay public so clients can authenticate.

    Args:
        request (Request): The incoming request.
        call_next: The next handler in the middleware chain.

    Returns:
        Response: A 401 JSON response, or the downstream response.
    """
    path = request.url.path
    guarded = path.startswith("/api") or path.startswith(settings.media_url)
    if guarded and auth_state.auth_required and path not in _PUBLIC_API_PATHS:
        token = request.cookies.get(SESSION_COOKIE, "")
        if not (token and verify_session_token(token, auth_state.session_secret)):
            return JSONResponse(status_code=401, content={"detail": "PIN necessário."})
    return await call_next(request)


@app.exception_handler(ServiceError)
async def handle_service_error(request: Request, exc: ServiceError) -> JSONResponse:
    """Translate domain errors into JSON HTTP responses.

    Args:
        request (Request): The incoming request.
        exc (ServiceError): The raised domain error.

    Returns:
        JSONResponse: A response carrying the error's status and message.
    """
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Report service liveness.

    Returns:
        dict[str, str]: A simple status payload.
    """
    return {"status": "ok"}


app.include_router(api_router)

# Serve uploaded images. The directory is created if it does not exist.
Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
app.mount(settings.media_url, StaticFiles(directory=settings.media_dir), name="media")
