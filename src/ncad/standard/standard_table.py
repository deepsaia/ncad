"""Load a versioned standard-part dimension table and look up one designation's dimensions.

A standard part's dimensions are DATA, not code: each family ships a JSON table (see
``standard_tables/``) keyed by designation (``M8``, ...), carrying its standard name, version, and a
provenance/source note. This loads one such table and hands a generator the dimensions for a
requested designation, so the numbers and the geometry stay separate (a table edit never touches a
generator). One class; loading happens once at construction.

Table shape: ``{"standard", "title", "version", "source", "unit", "designations": {<key>: {..}}}``.
"""

import os

from ncad.spec.spec_loader import SpecLoader

# The shipped tables live beside this module, one file per standard family.
_TABLE_DIR = os.path.join(os.path.dirname(__file__), "standard_tables")


class StandardTable:
    """A loaded dimension table for one standard family, queryable by designation."""

    def __init__(self, file_name: str) -> None:
        self._path = os.path.join(_TABLE_DIR, file_name)
        self._data = SpecLoader().load(self._path)

    @property
    def standard(self) -> str:
        """The standard's designation string (e.g. ``ISO 7089``)."""
        return str(self._data.get("standard", "unknown"))

    @property
    def version(self) -> str:
        """The table file's version string (for provenance)."""
        return str(self._data.get("version", "unknown"))

    @property
    def source(self) -> str:
        """The table's human-readable source/attribution note."""
        return str(self._data.get("source", ""))

    def designations(self) -> list[str]:
        """The designation keys this table defines (``M3``, ``M4``, ...)."""
        return list(self._data.get("designations", {}).keys())

    def dimensions(self, designation: str) -> dict[str, float]:
        """The dimension dict for ``designation``; raises KeyError listing known keys if absent."""
        table = self._data.get("designations", {})
        if designation not in table:
            raise KeyError(
                f"unknown {self.standard} designation {designation!r}; known: "
                f"{sorted(table.keys())}")
        return dict(table[designation])
