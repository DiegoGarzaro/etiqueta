"""Pydantic schemas for PIN authentication."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Payload to sign in with the access PIN.

    Attributes:
        pin (str): The PIN (4-8 digits).
    """

    pin: str = Field(min_length=4, max_length=8, pattern=r"^\d+$")


class PinChangeRequest(BaseModel):
    """Payload to set or change the access PIN.

    Attributes:
        current_pin (str | None): The current PIN; required when one is set.
        new_pin (str): The new PIN (4-8 digits).
    """

    current_pin: str | None = None
    new_pin: str = Field(min_length=4, max_length=8, pattern=r"^\d+$")


class AuthStatus(BaseModel):
    """Whether authentication is configured and satisfied.

    Attributes:
        auth_required (bool): ``True`` when a PIN is configured.
        authenticated (bool): ``True`` when the request carries a valid session.
    """

    auth_required: bool
    authenticated: bool
