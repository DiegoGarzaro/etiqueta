"""Tests for the SLP650 client, label rendering, and print routes."""

import json
from io import BytesIO

import httpx
import pytest
from PIL import Image

from app.api.routes.printing import get_print_client
from app.main import app
from app.models.location import LocationType
from app.services.label_image import MEDIA_BADGE_CANVAS, render_location_label
from app.services.slp650 import (
    PrinterUnavailableError,
    PrintRequestError,
    Slp650Client,
)


def make_client(handler) -> Slp650Client:
    """Build a client whose HTTP layer is a mock transport.

    Args:
        handler: Function mapping a request to a mocked response.

    Returns:
        Slp650Client: A client that never touches the network.
    """
    return Slp650Client(
        base_url="http://printserver:8787",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )


class TestLabelRendering:
    """The rendered label must satisfy the SDK's design rules."""

    def test_canvas_and_purity(self) -> None:
        png = render_location_label(
            "ARM-A · GAV-02",
            "Gaveta de ferramentas",
            LocationType.GAVETA,
            "http://server:8080/locais/abc",
        )
        image = Image.open(BytesIO(png))
        assert image.size == MEDIA_BADGE_CANVAS
        assert image.mode == "1"
        colors = {color for _, color in image.convert("L").getcolors()}
        assert colors <= {0, 255}

    def test_long_name_wraps_without_error(self) -> None:
        png = render_location_label(
            "CMD-01 · ARM-B · PRT-03 · CX-12",
            "Caixa de enfeites de natal e decorações antigas",
            LocationType.CAIXA,
            "http://server:8080/locais/abc",
        )
        assert Image.open(BytesIO(png)).size == MEDIA_BADGE_CANVAS


class TestSlp650Client:
    """Error responses from the print server map to readable domain errors."""

    async def test_health_ok(self) -> None:
        client = make_client(
            lambda request: httpx.Response(200, json={"ok": True, "pdf_support": False})
        )
        health = await client.health()
        assert health.ok is True

    async def test_sends_api_key_header(self) -> None:
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["key"] = request.headers.get("X-API-Key", "")
            return httpx.Response(200, json={"ok": True})

        await make_client(handler).health()
        assert seen["key"] == "test-key"

    async def test_missing_key_is_configuration_error(self) -> None:
        client = Slp650Client(base_url="http://printserver:8787", api_key="")
        with pytest.raises(PrinterUnavailableError, match="SLP650_API_KEY"):
            await client.health()

    async def test_422_maps_to_readable_error(self) -> None:
        client = make_client(
            lambda request: httpx.Response(422, json={"detail": "unknown media 'Bogus'"})
        )
        with pytest.raises(PrintRequestError, match="unknown media"):
            await client.print_template("visitor-badge", {"name": "X"})

    async def test_503_maps_to_printer_offline(self) -> None:
        client = make_client(
            lambda request: httpx.Response(503, json={"detail": "printer not connected"})
        )
        with pytest.raises(PrinterUnavailableError, match="printer not connected"):
            await client.print_template("visitor-badge", {"name": "X"})

    async def test_connection_error_maps_to_unavailable(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with pytest.raises(PrinterUnavailableError, match="inacessível"):
            await make_client(handler).health()


class TestPrintRoutes:
    """Routes proxy the print server and enforce upload validation."""

    @staticmethod
    def override(handler) -> None:
        app.dependency_overrides[get_print_client] = lambda: make_client(handler)

    def teardown_method(self) -> None:
        app.dependency_overrides.pop(get_print_client, None)

    async def test_badge_forwards_fields(self, client: httpx.AsyncClient) -> None:
        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured.update(json.loads(request.content))
            return httpx.Response(200, json={"engine": "native"})

        self.override(handler)
        response = await client.post(
            "/api/print/badge",
            json={"name": "Diego", "company": "ACME", "copies": 2},
        )
        assert response.status_code == 200
        assert response.json()["engine"] == "native"
        assert captured == {
            "template": "visitor-badge",
            "fields": {"name": "Diego", "company": "ACME"},
            "copies": 2,
        }

    async def test_image_rejects_non_image(self, client: httpx.AsyncClient) -> None:
        self.override(lambda request: httpx.Response(200, json={"engine": "native"}))
        response = await client.post(
            "/api/print/image", files={"file": ("notes.txt", b"hi", "text/plain")}
        )
        assert response.status_code == 422
        assert "PNG" in response.json()["detail"]

    async def test_printer_offline_returns_503(self, client: httpx.AsyncClient) -> None:
        self.override(
            lambda request: httpx.Response(503, json={"detail": "printer not connected"})
        )
        response = await client.post("/api/print/badge", json={"name": "Diego"})
        assert response.status_code == 503

    async def test_qr_base_prefers_public_base_url_setting(
        self, client: httpx.AsyncClient, monkeypatch
    ) -> None:
        from app.core.config import get_settings

        created = await client.post(
            "/api/locations", json={"name": "Caixa", "type": "caixa"}
        )
        location_id = created.json()["id"]

        # Without a setting and without qr_base_url there is nothing to encode.
        response = await client.get(f"/api/print/locations/{location_id}/preview.png")
        assert response.status_code == 422
        assert "INV_PUBLIC_BASE_URL" in response.json()["detail"]

        # With the setting, qr_base_url becomes optional.
        monkeypatch.setattr(get_settings(), "public_base_url", "http://10.0.0.228:8080")
        response = await client.get(f"/api/print/locations/{location_id}/preview.png")
        assert response.status_code == 200
        config = await client.get("/api/config")
        assert config.json() == {"public_base_url": "http://10.0.0.228:8080"}

    async def test_location_label_print_and_preview(self, client: httpx.AsyncClient) -> None:
        created = await client.post(
            "/api/locations", json={"name": "Armário do escritório", "type": "armario"}
        )
        location_id = created.json()["id"]

        preview = await client.get(
            f"/api/print/locations/{location_id}/preview.png",
            params={"qr_base_url": "http://server:8080"},
        )
        assert preview.status_code == 200
        assert Image.open(BytesIO(preview.content)).size == MEDIA_BADGE_CANVAS

        uploads: list[tuple[str, bytes]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            uploads.append((request.url.path, request.content))
            return httpx.Response(200, json={"engine": "native"})

        self.override(handler)
        response = await client.post(
            f"/api/print/locations/{location_id}",
            json={"qr_base_url": "http://server:8080", "copies": 1},
        )
        assert response.status_code == 200
        assert uploads[0][0] == "/print/image"
        assert b"MediaBadge" in uploads[0][1]
