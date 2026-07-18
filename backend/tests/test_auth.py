"""Tests for PIN authentication: login, lockout, guarding, and PIN change."""

from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio

from app.services.auth import auth_state, hash_pin, rate_limiter


@pytest_asyncio.fixture
async def pin_client(client: httpx.AsyncClient) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide the app client with PIN "1234" enforced, restoring state after.

    Args:
        client (httpx.AsyncClient): The base app client fixture.

    Yields:
        httpx.AsyncClient: The same client, with auth enabled process-wide.
    """
    previous_hash = auth_state.pin_hash
    auth_state.pin_hash = hash_pin("1234")
    rate_limiter.reset()
    yield client
    auth_state.pin_hash = previous_hash
    rate_limiter.reset()


class TestOpenMode:
    """Without a configured PIN the app stays open (dev/first-run)."""

    async def test_api_open_and_status_reports_no_auth(self, client: httpx.AsyncClient) -> None:
        assert (await client.get("/api/locations/tree")).status_code == 200
        status = (await client.get("/api/auth/status")).json()
        assert status == {"auth_required": False, "authenticated": False}

    async def test_first_pin_set_requires_no_current(self, client: httpx.AsyncClient) -> None:
        previous_hash = auth_state.pin_hash
        try:
            response = await client.post("/api/auth/pin", json={"new_pin": "4321"})
            assert response.status_code == 204
            assert auth_state.auth_required
            # The setter received a session cookie and stays signed in.
            assert (await client.get("/api/locations/tree")).status_code == 200
        finally:
            auth_state.pin_hash = previous_hash
            client.cookies.clear()


class TestPinEnforcement:
    """With a PIN configured, API and login flows behave correctly."""

    async def test_api_requires_session(self, pin_client: httpx.AsyncClient) -> None:
        response = await pin_client.get("/api/locations/tree")
        assert response.status_code == 401

    async def test_auth_endpoints_stay_public(self, pin_client: httpx.AsyncClient) -> None:
        assert (await pin_client.get("/api/auth/status")).status_code == 200
        assert (await pin_client.post("/api/auth/logout")).status_code == 204

    async def test_wrong_pin_rejected(self, pin_client: httpx.AsyncClient) -> None:
        response = await pin_client.post("/api/auth/login", json={"pin": "0000"})
        assert response.status_code == 401

    async def test_login_grants_access_and_logout_revokes(
        self, pin_client: httpx.AsyncClient
    ) -> None:
        assert (await pin_client.post("/api/auth/login", json={"pin": "1234"})).status_code == 204
        assert (await pin_client.get("/api/locations/tree")).status_code == 200
        status = (await pin_client.get("/api/auth/status")).json()
        assert status == {"auth_required": True, "authenticated": True}

        await pin_client.post("/api/auth/logout")
        assert (await pin_client.get("/api/locations/tree")).status_code == 401

    async def test_lockout_after_repeated_failures(self, pin_client: httpx.AsyncClient) -> None:
        for _ in range(5):
            response = await pin_client.post("/api/auth/login", json={"pin": "9999"})
        response = await pin_client.post("/api/auth/login", json={"pin": "1234"})
        assert response.status_code == 429
        assert "Tente novamente" in response.json()["detail"]

    async def test_change_pin_rotates_sessions(self, pin_client: httpx.AsyncClient) -> None:
        await pin_client.post("/api/auth/login", json={"pin": "1234"})
        old_cookie = pin_client.cookies.get("inv_session")

        response = await pin_client.post(
            "/api/auth/pin", json={"current_pin": "1234", "new_pin": "5678"}
        )
        assert response.status_code == 204
        # The caller got a fresh cookie and keeps access.
        assert pin_client.cookies.get("inv_session") != old_cookie
        assert (await pin_client.get("/api/locations/tree")).status_code == 200
        # The old token no longer validates (secret was rotated).
        pin_client.cookies.set("inv_session", old_cookie)
        assert (await pin_client.get("/api/locations/tree")).status_code == 401

    async def test_change_pin_needs_current(self, pin_client: httpx.AsyncClient) -> None:
        await pin_client.post("/api/auth/login", json={"pin": "1234"})
        response = await pin_client.post(
            "/api/auth/pin", json={"current_pin": "0000", "new_pin": "5678"}
        )
        assert response.status_code == 401

    async def test_new_pin_must_be_digits(self, pin_client: httpx.AsyncClient) -> None:
        await pin_client.post("/api/auth/login", json={"pin": "1234"})
        response = await pin_client.post(
            "/api/auth/pin", json={"current_pin": "1234", "new_pin": "abcd"}
        )
        assert response.status_code == 422
