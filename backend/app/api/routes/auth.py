"""PIN login, logout, status, and PIN management endpoints."""

from fastapi import APIRouter, Request, Response, status

from app.api.deps import SessionDep
from app.schemas.auth import AuthStatus, LoginRequest, PinChangeRequest
from app.services.auth import (
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    AuthService,
    auth_state,
    verify_session_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    """Attach the session cookie to a response.

    Args:
        response (Response): The outgoing response.
        token (str): The signed session token.
    """
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        path="/",
    )


@router.get("/status", response_model=AuthStatus)
async def auth_status(request: Request) -> AuthStatus:
    """Report whether a PIN is required and whether this session is valid.

    Args:
        request (Request): The incoming request (session cookie is read).

    Returns:
        AuthStatus: The authentication state for this client.
    """
    token = request.cookies.get(SESSION_COOKIE, "")
    return AuthStatus(
        auth_required=auth_state.auth_required,
        authenticated=bool(token) and verify_session_token(token, auth_state.session_secret),
    )


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(data: LoginRequest, response: Response, session: SessionDep) -> None:
    """Sign in with the PIN, setting the session cookie.

    Args:
        data (LoginRequest): The submitted PIN.
        response (Response): The outgoing response (cookie is set).
        session (SessionDep): Database session.
    """
    _set_session_cookie(response, AuthService(session).login(data.pin))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Sign out by clearing the session cookie.

    Args:
        response (Response): The outgoing response (cookie is cleared).
    """
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.post("/pin", status_code=status.HTTP_204_NO_CONTENT)
async def change_pin(data: PinChangeRequest, response: Response, session: SessionDep) -> None:
    """Set or change the access PIN.

    Changing the PIN signs out all other devices; this client receives a
    fresh session cookie. When no PIN is configured yet, this sets the first
    one (first-run setup).

    Args:
        data (PinChangeRequest): Current and new PIN.
        response (Response): The outgoing response (fresh cookie is set).
        session (SessionDep): Database session.
    """
    token = await AuthService(session).change_pin(data.current_pin, data.new_pin)
    _set_session_cookie(response, token)
