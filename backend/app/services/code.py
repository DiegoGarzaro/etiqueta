"""Generation of human-readable location code segments (e.g. ARM-A, GAV-02)."""

import string

from app.models.location import LocationType
from app.repositories.location import LocationRepository

PREFIXES: dict[LocationType, str] = {
    LocationType.COMODO: "CMD",
    LocationType.ARMARIO: "ARM",
    LocationType.GAVETA: "GAV",
    LocationType.PRATELEIRA: "PRT",
    LocationType.CAIXA: "CX",
    LocationType.ORGANIZADOR: "ORG",
}


class CodeService:
    """Generates unique code segments for a location within its parent.

    Armários are lettered (A, B, C, …) to match the label style ``ARM-A``;
    every other type is numbered and zero-padded, e.g. ``GAV-02``.
    """

    def __init__(self, repository: LocationRepository) -> None:
        """Initialize the service.

        Args:
            repository (LocationRepository): Repository used to inspect siblings.
        """
        self.repository = repository

    async def generate(self, parent_id: str | None, type_: LocationType) -> str:
        """Generate a code segment unique among the parent's children.

        Args:
            parent_id (str | None): Parent location id, or ``None`` for a root cômodo.
            type_ (LocationType): The type of the new location.

        Returns:
            str: A code segment such as ``"ARM-A"`` or ``"GAV-02"``.
        """
        prefix = PREFIXES[type_]
        siblings = await self.repository.get_children(parent_id)
        existing_codes = {sibling.code for sibling in siblings}
        index = sum(1 for sibling in siblings if sibling.type == type_)
        while True:
            code = f"{prefix}-{self._suffix(type_, index)}"
            if code not in existing_codes:
                return code
            index += 1

    @staticmethod
    def _suffix(type_: LocationType, index: int) -> str:
        """Return the suffix for a given type and zero-based index.

        Args:
            type_ (LocationType): The location type.
            index (int): Zero-based position among same-type siblings.

        Returns:
            str: A letter for armários, otherwise a zero-padded number.
        """
        if type_ == LocationType.ARMARIO:
            return CodeService._letter(index)
        return f"{index + 1:02d}"

    @staticmethod
    def _letter(index: int) -> str:
        """Convert a zero-based index to a spreadsheet-style letter code.

        Args:
            index (int): Zero-based index (0 -> "A", 26 -> "AA").

        Returns:
            str: The uppercase letter code.
        """
        letters = ""
        value = index + 1
        while value > 0:
            value, remainder = divmod(value - 1, 26)
            letters = string.ascii_uppercase[remainder] + letters
        return letters
