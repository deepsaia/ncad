"""Facade over the standard-part families: designation -> a buildable ncad part document.

The single entry point for standard parts. It owns the registry that binds a family key (``washer``,
``hex_nut``) to its dimension table (StandardTable) and its geometry generator, so a caller asks for
``generate("hex_nut", "M8")`` without knowing which table or generator serves it. Generation is
lookup + generate: the table supplies the dimensions, the generator turns them into a part document.
Everything is produced natively (no network, no third-party CAD import). One class.
"""

from collections.abc import Callable
from typing import Any

from ncad.standard.hex_nut_generator import HexNutGenerator
from ncad.standard.standard_table import StandardTable
from ncad.standard.washer_generator import WasherGenerator

# Family key -> (table file name, generator factory, required dimension keys). New families slot in
# here with a table + a generator + their required dims; the CLI and callers need no change. The
# required keys let the custom-dimensions path reject an incomplete spec with a clear error.
_FAMILIES: dict[str, tuple[str, Callable[[], Any], tuple[str, ...]]] = {
    "washer": ("iso_7089_washers.json", WasherGenerator,
               ("inner_diameter", "outer_diameter", "thickness")),
    "hex_nut": ("iso_4032_hex_nuts.json", HexNutGenerator,
                ("thread_diameter", "width_across_flats", "thickness")),
}


class StandardLibrary:
    """Generates standard-part documents by family + designation from versioned tables."""

    def families(self) -> list[str]:
        """The standard-part families this library can generate."""
        return sorted(_FAMILIES.keys())

    def designations(self, family: str) -> list[str]:
        """The designation keys available for ``family`` (``M3``, ``M4``, ...)."""
        return self._table(family).designations()

    def required_dimensions(self, family: str) -> tuple[str, ...]:
        """The dimension keys ``family`` needs (for the custom-dimensions path and help text)."""
        return self._family(family)[2]

    def generate(self, family: str, designation: str, part_name: str | None = None) -> dict:
        """Return a one-part ncad document for a standard ``family``/``designation`` (table lookup).

        ``part_name`` defaults to ``<family>_<designation>`` lowercased (e.g. ``hex_nut_m8``).
        """
        table_file, _, _ = self._family(family)
        dimensions = StandardTable(table_file).dimensions(designation)
        name = part_name or f"{family}_{designation}".lower()
        return self._build_document(family, name, dimensions)

    def generate_custom(self, family: str, dimensions: dict, part_name: str | None = None) -> dict:
        """Return a one-part document for ``family`` from CALLER-supplied dimensions (no table).

        The second entry path: a non-standard size. ``dimensions`` must carry every key in
        ``required_dimensions(family)``; a missing key raises ValueError. ``part_name`` defaults to
        ``<family>_custom``.
        """
        missing = [k for k in self.required_dimensions(family) if k not in dimensions]
        if missing:
            raise ValueError(
                f"custom {family} needs dimensions {list(self.required_dimensions(family))}; "
                f"missing {missing}")
        name = part_name or f"{family}_custom"
        return self._build_document(family, name, dimensions)

    def provenance(self, family: str) -> dict[str, str]:
        """The standard/version/source for ``family`` (for a report or sidecar)."""
        table = self._table(family)
        return {"standard": table.standard, "version": table.version, "source": table.source}

    def _build_document(self, family: str, part_name: str, dimensions: dict) -> dict:
        """Run ``family``'s generator over ``dimensions`` into a part document."""
        _, generator_factory, _ = self._family(family)
        return generator_factory().generate(part_name, dimensions)

    def _family(self, family: str) -> tuple[str, Callable[[], Any], tuple[str, ...]]:
        """The registry entry for ``family``; raises KeyError listing known keys if absent."""
        if family not in _FAMILIES:
            raise KeyError(
                f"unknown standard-part family {family!r}; known: {sorted(_FAMILIES.keys())}")
        return _FAMILIES[family]

    def _table(self, family: str) -> StandardTable:
        """The loaded StandardTable for ``family``."""
        return StandardTable(self._family(family)[0])
