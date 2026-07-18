"""End-to-end API tests over the walking skeleton."""

import io

from httpx import AsyncClient
from PIL import Image


def _png_bytes(color: str = "green") -> bytes:
    """Return the bytes of a tiny in-memory PNG.

    Args:
        color (str): Fill color for the test image.

    Returns:
        bytes: Encoded PNG data.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (24, 24), color).save(buffer, "PNG")
    return buffer.getvalue()


async def _create_location(
    client: AsyncClient, name: str, type_: str, parent_id: str | None = None
) -> dict:
    """Create a location and return its JSON body.

    Args:
        client (AsyncClient): The test client.
        name (str): Location name.
        type_ (str): Location type value.
        parent_id (str | None): Optional parent id.

    Returns:
        dict: The created location payload.
    """
    response = await client.post(
        "/api/locations",
        json={"name": name, "type": type_, "parent_id": parent_id},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_health(client: AsyncClient) -> None:
    """The health endpoint reports ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_location_codes_and_full_code(client: AsyncClient) -> None:
    """Codes follow the label style and full_code joins non-room ancestors."""
    room = await _create_location(client, "Escritório", "comodo")
    wardrobe = await _create_location(client, "Armário A", "armario", room["id"])
    drawer = await _create_location(client, "Gaveta 2", "gaveta", wardrobe["id"])

    assert wardrobe["code"] == "ARM-A"
    assert drawer["code"] == "GAV-01"
    assert drawer["full_code"] == "ARM-A · GAV-01"
    # path includes the room, tag (full_code) excludes it.
    assert [segment["name"] for segment in drawer["path"]] == [
        "Escritório",
        "Armário A",
        "Gaveta 2",
    ]


async def test_item_lifecycle_and_counts(client: AsyncClient) -> None:
    """Creating an item surfaces its location tag and updates subtree counts."""
    room = await _create_location(client, "Cozinha", "comodo")
    box = await _create_location(client, "Caixa 1", "caixa", room["id"])

    category = (
        await client.post("/api/categories", json={"name": "Eletrônicos", "color": "#2F6B4F"})
    ).json()

    created = await client.post(
        "/api/items",
        json={
            "name": "Carregador USB-C",
            "quantity": 2,
            "location_id": box["id"],
            "category_ids": [category["id"]],
        },
    )
    assert created.status_code == 201, created.text
    item = created.json()
    assert item["location"]["full_code"] == "CX-01"
    assert item["categories"][0]["name"] == "Eletrônicos"

    tree = (await client.get("/api/locations/tree")).json()
    assert tree[0]["total_item_count"] == 1
    assert tree[0]["children"][0]["direct_item_count"] == 1


async def test_search_is_accent_insensitive(client: AsyncClient) -> None:
    """Searching without accents finds accented item names."""
    room = await _create_location(client, "Sala", "comodo")
    shelf = await _create_location(client, "Prateleira", "prateleira", room["id"])
    await client.post(
        "/api/items", json={"name": "Câmera fotográfica", "location_id": shelf["id"]}
    )

    results = (await client.get("/api/search", params={"q": "camera"})).json()
    assert results["total"] == 1
    assert results["items"][0]["name"] == "Câmera fotográfica"


async def test_update_and_move_item(client: AsyncClient) -> None:
    """Editing an item changes its fields and moving it changes the location tag."""
    room = await _create_location(client, "Cozinha", "comodo")
    box_a = await _create_location(client, "Caixa 1", "caixa", room["id"])
    box_b = await _create_location(client, "Caixa 2", "caixa", room["id"])

    item = (
        await client.post(
            "/api/items", json={"name": "Fita", "quantity": 1, "location_id": box_a["id"]}
        )
    ).json()

    updated = await client.patch(
        f"/api/items/{item['id']}",
        json={"name": "Fita adesiva", "quantity": 3, "location_id": box_b["id"]},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["name"] == "Fita adesiva"
    assert body["quantity"] == 3
    assert body["location"]["full_code"] == "CX-02"


async def test_move_location_updates_full_code(client: AsyncClient) -> None:
    """Moving a location under a new parent recomputes its tag path."""
    room = await _create_location(client, "Escritório", "comodo")
    wardrobe_a = await _create_location(client, "Armário A", "armario", room["id"])
    wardrobe_b = await _create_location(client, "Armário B", "armario", room["id"])
    drawer = await _create_location(client, "Gaveta 1", "gaveta", wardrobe_a["id"])
    assert drawer["full_code"] == "ARM-A · GAV-01"

    moved = await client.patch(
        f"/api/locations/{drawer['id']}", json={"parent_id": wardrobe_b["id"]}
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["full_code"] == "ARM-B · GAV-01"


async def test_move_location_into_descendant_rejected(client: AsyncClient) -> None:
    """A location cannot be moved inside one of its own descendants."""
    room = await _create_location(client, "Sala", "comodo")
    wardrobe = await _create_location(client, "Armário", "armario", room["id"])
    drawer = await _create_location(client, "Gaveta", "gaveta", wardrobe["id"])

    rejected = await client.patch(
        f"/api/locations/{wardrobe['id']}", json={"parent_id": drawer["id"]}
    )
    assert rejected.status_code == 422


async def test_upload_and_delete_item_photo(client: AsyncClient) -> None:
    """Uploading attaches a photo with URLs; deleting removes it."""
    room = await _create_location(client, "Quarto", "comodo")
    box = await _create_location(client, "Caixa 1", "caixa", room["id"])
    item = (
        await client.post("/api/items", json={"name": "Fone", "location_id": box["id"]})
    ).json()

    upload = await client.post(
        f"/api/items/{item['id']}/photos",
        files={"file": ("foto.png", _png_bytes(), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    photo = upload.json()
    assert photo["url"].startswith("/media/")
    assert photo["thumb_url"].startswith("/media/")

    fetched = (await client.get(f"/api/items/{item['id']}")).json()
    assert len(fetched["photos"]) == 1

    deleted = await client.delete(f"/api/photos/{photo['id']}")
    assert deleted.status_code == 204
    after = (await client.get(f"/api/items/{item['id']}")).json()
    assert after["photos"] == []


async def test_upload_invalid_image_rejected(client: AsyncClient) -> None:
    """Non-image bytes are rejected with a 422."""
    room = await _create_location(client, "Sala", "comodo")
    item = (
        await client.post("/api/items", json={"name": "Livro", "location_id": room["id"]})
    ).json()

    response = await client.post(
        f"/api/items/{item['id']}/photos",
        files={"file": ("nope.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 422


async def test_export_import_round_trip(client: AsyncClient) -> None:
    """Exporting then importing restores the same inventory, searchable."""
    room = await _create_location(client, "Escritório", "comodo")
    drawer = await _create_location(client, "Gaveta 2", "gaveta", room["id"])
    category = (
        await client.post("/api/categories", json={"name": "Eletrônicos", "color": "#2F6B4F"})
    ).json()
    await client.post(
        "/api/items",
        json={
            "name": "Câmera",
            "location_id": drawer["id"],
            "category_ids": [category["id"]],
        },
    )

    backup = (await client.get("/api/export")).json()
    assert len(backup["locations"]) == 2
    assert len(backup["items"]) == 1

    result = await client.post("/api/import", json=backup)
    assert result.status_code == 200, result.text
    assert result.json() == {"categories": 1, "locations": 2, "items": 1, "photos": 0}

    # Data is intact and still searchable after the restore.
    tree = (await client.get("/api/locations/tree")).json()
    assert len(tree) == 1
    found = (await client.get("/api/search", params={"q": "camera"})).json()
    assert found["total"] == 1
    assert found["items"][0]["location"]["full_code"] == "GAV-01"


async def test_export_csv_has_items(client: AsyncClient) -> None:
    """The CSV export lists items with their location code."""
    room = await _create_location(client, "Cozinha", "comodo")
    box = await _create_location(client, "Caixa 1", "caixa", room["id"])
    await client.post("/api/items", json={"name": "Panela", "location_id": box["id"]})

    response = await client.get("/api/export.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    body = response.text
    assert "Item,Quantidade" in body
    assert "Panela" in body
    assert "CX-01" in body


async def test_delete_non_empty_location_conflicts(client: AsyncClient) -> None:
    """Deleting a non-empty location is refused unless forced."""
    room = await _create_location(client, "Quarto", "comodo")
    await _create_location(client, "Armário", "armario", room["id"])

    refused = await client.delete(f"/api/locations/{room['id']}")
    assert refused.status_code == 409

    forced = await client.delete(f"/api/locations/{room['id']}", params={"force": "true"})
    assert forced.status_code == 204
