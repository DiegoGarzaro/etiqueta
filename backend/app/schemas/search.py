"""Pydantic schemas for search results."""

from pydantic import BaseModel

from app.schemas.item import ItemRead


class SearchResults(BaseModel):
    """Result set for a global search query.

    Attributes:
        query (str): The original query string.
        total (int): Number of matching items.
        items (list[ItemRead]): Matching items with their locations.
    """

    query: str
    total: int
    items: list[ItemRead] = []
