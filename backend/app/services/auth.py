"""PIN authentication: hashed PIN, signed session cookies, and rate limiting.

Single-user model: one PIN protects the whole app. The PIN hash and the
session-signing secret live in the ``app_settings`` table; ``INV_APP_PIN``
seeds the PIN on first boot. Both are cached in-process (``auth_state``) so
the request middleware never touches the database.
"""

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.app_setting import AppSetting
from app.services.errors import TooManyAttemptsError, UnauthorizedError, ValidationError

SESSION_COOKIE = "inv_session"
SESSION_TTL_SECONDS = 90 * 24 * 3600

_PIN_HASH_KEY = "pin_hash"
_SESSION_SECRET_KEY = "session_secret"


@dataclass
class AuthState:
    """In-process cache of the auth configuration.

    Attributes:
        pin_hash (str | None): Salted PIN hash, or ``None`` when no PIN is set
            (authentication disabled).
        session_secret (str): Secret used to sign session tokens.
    """

    pin_hash: str | None = None
    session_secret: str = field(default_factory=lambda: secrets.token_hex(32))

    @property
    def auth_required(self) -> bool:
        """Whether requests must carry a valid session.

        Returns:
            bool: ``True`` when a PIN is configured.
        """
        return self.pin_hash is not None


auth_state = AuthState()
"""Process-wide auth configuration, loaded at startup."""


class PinRateLimiter:
    """Locks PIN attempts after repeated failures (brute-force protection)."""

    def __init__(self, max_failures: int = 5, lockout_seconds: int = 30) -> None:
        """Initialize the limiter.

        Args:
            max_failures (int): Failures allowed before locking out.
            lockout_seconds (int): Lockout duration once exceeded.
        """
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        self.failures = 0
        self.locked_until = 0.0

    def retry_in(self) -> int:
        """Return the seconds remaining in the current lockout.

        Returns:
            int: Seconds to wait, or ``0`` when attempts are allowed.
        """
        return max(0, int(self.locked_until - time.monotonic()) + 1) if self.locked() else 0

    def locked(self) -> bool:
        """Whether attempts are currently locked out.

        Returns:
            bool: ``True`` while the lockout window is active.
        """
        return time.monotonic() < self.locked_until

    def record_failure(self) -> None:
        """Count a failed attempt, starting a lockout when the limit is hit."""
        self.failures += 1
        if self.failures >= self.max_failures:
            self.failures = 0
            self.locked_until = time.monotonic() + self.lockout_seconds

    def reset(self) -> None:
        """Clear failures and any active lockout (after a successful login)."""
        self.failures = 0
        self.locked_until = 0.0


rate_limiter = PinRateLimiter()
"""Process-wide limiter. Global (not per-IP) on purpose: single-user app."""


def hash_pin(pin: str, salt: str | None = None) -> str:
    """Hash a PIN with a random salt.

    Args:
        pin (str): The plain PIN.
        salt (str | None): Salt override; a random one is generated if omitted.

    Returns:
        str: ``"salt$hexdigest"``.
    """
    salt = salt or secrets.token_hex(8)
    digest = hashlib.sha256(f"{salt}:{pin}".encode()).hexdigest()
    return f"{salt}${digest}"


def verify_pin(pin: str, pin_hash: str) -> bool:
    """Check a PIN against a stored hash in constant time.

    Args:
        pin (str): The plain PIN to check.
        pin_hash (str): Stored ``"salt$hexdigest"`` value.

    Returns:
        bool: ``True`` when the PIN matches.
    """
    salt, _, _ = pin_hash.partition("$")
    return hmac.compare_digest(hash_pin(pin, salt), pin_hash)


def create_session_token(secret: str, ttl_seconds: int = SESSION_TTL_SECONDS) -> str:
    """Create a signed, stateless session token.

    Args:
        secret (str): Signing secret.
        ttl_seconds (int): Token lifetime.

    Returns:
        str: ``"expiry.signature"``.
    """
    expiry = str(int(time.time()) + ttl_seconds)
    signature = hmac.new(secret.encode(), expiry.encode(), hashlib.sha256).hexdigest()
    return f"{expiry}.{signature}"


def verify_session_token(token: str, secret: str) -> bool:
    """Validate a session token's signature and expiry.

    Args:
        token (str): The cookie value.
        secret (str): Signing secret.

    Returns:
        bool: ``True`` for a valid, unexpired token.
    """
    expiry, _, signature = token.partition(".")
    if not expiry.isdigit() or int(expiry) < time.time():
        return False
    expected = hmac.new(secret.encode(), expiry.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


async def load_auth_state(session: AsyncSession) -> None:
    """Load (or seed) the auth configuration into ``auth_state`` at startup.

    The session secret is generated and persisted on first boot so sessions
    survive restarts. ``INV_APP_PIN`` seeds the PIN only when none is stored.

    Args:
        session (AsyncSession): Database session.
    """
    rows = {
        row.key: row.value for row in (await session.execute(select(AppSetting))).scalars()
    }
    if _SESSION_SECRET_KEY not in rows:
        rows[_SESSION_SECRET_KEY] = secrets.token_hex(32)
        session.add(AppSetting(key=_SESSION_SECRET_KEY, value=rows[_SESSION_SECRET_KEY]))
    env_pin = get_settings().app_pin
    if _PIN_HASH_KEY not in rows and env_pin:
        rows[_PIN_HASH_KEY] = hash_pin(env_pin)
        session.add(AppSetting(key=_PIN_HASH_KEY, value=rows[_PIN_HASH_KEY]))
    await session.commit()
    auth_state.session_secret = rows[_SESSION_SECRET_KEY]
    auth_state.pin_hash = rows.get(_PIN_HASH_KEY)


class AuthService:
    """Login and PIN management."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.

        Args:
            session (AsyncSession): The active database session.
        """
        self.session = session

    def login(self, pin: str) -> str:
        """Verify a PIN and issue a session token.

        Args:
            pin (str): The submitted PIN.

        Returns:
            str: A signed session token for the cookie.

        Raises:
            TooManyAttemptsError: While the lockout window is active.
            UnauthorizedError: When the PIN is wrong or none is configured.
        """
        if rate_limiter.locked():
            raise TooManyAttemptsError(
                f"Muitas tentativas. Tente novamente em {rate_limiter.retry_in()}s."
            )
        if auth_state.pin_hash is None or not verify_pin(pin, auth_state.pin_hash):
            rate_limiter.record_failure()
            raise UnauthorizedError("PIN incorreto.")
        rate_limiter.reset()
        return create_session_token(auth_state.session_secret)

    async def change_pin(self, current_pin: str | None, new_pin: str) -> str:
        """Set or change the PIN, rotating the session secret.

        Rotating the secret signs out every device; the caller receives a
        fresh token so it stays signed in.

        Args:
            current_pin (str | None): The current PIN; required when one is set.
            new_pin (str): The new PIN (4-8 digits).

        Returns:
            str: A fresh session token signed with the new secret.

        Raises:
            ValidationError: If the new PIN is not 4-8 digits.
            UnauthorizedError: If the current PIN is missing or wrong.
        """
        if not (new_pin.isdigit() and 4 <= len(new_pin) <= 8):
            raise ValidationError("O PIN deve ter de 4 a 8 dígitos.")
        if auth_state.pin_hash is not None:
            if current_pin is None or not verify_pin(current_pin, auth_state.pin_hash):
                raise UnauthorizedError("PIN atual incorreto.")
        new_hash = hash_pin(new_pin)
        new_secret = secrets.token_hex(32)
        await self._upsert(_PIN_HASH_KEY, new_hash)
        await self._upsert(_SESSION_SECRET_KEY, new_secret)
        await self.session.commit()
        auth_state.pin_hash = new_hash
        auth_state.session_secret = new_secret
        rate_limiter.reset()
        return create_session_token(new_secret)

    async def _upsert(self, key: str, value: str) -> None:
        """Insert or update one setting row.

        Args:
            key (str): Setting name.
            value (str): Setting value.
        """
        row = await self.session.get(AppSetting, key)
        if row is None:
            self.session.add(AppSetting(key=key, value=value))
        else:
            row.value = value
