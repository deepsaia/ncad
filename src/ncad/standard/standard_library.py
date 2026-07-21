"""Facade over the standard-part families: designation -> a buildable ncad part document.

The single entry point for standard parts. It owns the registry that binds a family key (``washer``,
``hex_nut``) to its dimension table (StandardTable) and its geometry generator, so a caller asks for
``generate("hex_nut", "M8")`` without knowing which table or generator serves it. Generation is
lookup + generate: the table supplies the dimensions, the generator turns them into a part document.
Everything is produced natively (no network, no third-party CAD import). One class.
"""

from collections.abc import Callable
from typing import Any

from ncad.standard.bearing_generator import BearingGenerator
from ncad.standard.elbow_generator import ElbowGenerator
from ncad.standard.flange_generator import FlangeGenerator
from ncad.standard.gasket_generator import GasketGenerator
from ncad.standard.hex_nut_generator import HexNutGenerator
from ncad.standard.i_beam_generator import IBeamGenerator
from ncad.standard.pipe_generator import PipeGenerator
from ncad.standard.reducer_generator import ReducerGenerator
from ncad.standard.standard_table import StandardTable
from ncad.standard.tee_generator import TeeGenerator
from ncad.standard.washer_generator import WasherGenerator

# Family key -> (table file name, generator factory, required dimension keys). New families slot in
# here with a table + a generator + their required dims; the CLI and callers need no change. The
# required keys let the custom-dimensions path reject an incomplete spec with a clear error. Each
# family is generatable BOTH by standard designation (table lookup) and by custom dimensions.
_BOLT_CIRCLE_DIMS = ("outer_diameter", "bore_diameter", "thickness",
                     "bolt_circle_diameter", "bolt_hole_diameter", "bolt_count")
_FAMILIES: dict[str, tuple[str, Callable[[], Any], tuple[str, ...]]] = {
    "washer": ("iso_7089_washers.json", WasherGenerator,
               ("inner_diameter", "outer_diameter", "thickness")),
    "hex_nut": ("iso_4032_hex_nuts.json", HexNutGenerator,
                ("thread_diameter", "width_across_flats", "thickness")),
    "pipe": ("en_10220_pipes.json", PipeGenerator,
             ("outer_diameter", "wall_thickness")),
    "flange": ("asme_b16_5_flanges.json", FlangeGenerator, _BOLT_CIRCLE_DIMS),
    "gasket": ("asme_b16_21_gaskets.json", GasketGenerator, _BOLT_CIRCLE_DIMS),
    "bearing": ("iso_15_bearings.json", BearingGenerator,
                ("outer_diameter", "bore_diameter", "width")),
    "i_beam": ("euronorm_ipe_beams.json", IBeamGenerator,
               ("height", "flange_width", "web_thickness", "flange_thickness")),
}

# Grouped families dispatch on a SUBTYPE (family -> subtype -> registry entry). The pipe_fitting
# family collects the pipe fittings (elbow/tee/reducer), each with its own table + generator. A
# grouped family is addressed as ``pipe_fitting`` + a subtype; new subtypes (cross, wye, cap) slot
# in here with a table + a generator, no facade change.
_SUBTYPED_FAMILIES: dict[str, dict[str, tuple[str, Callable[[], Any], tuple[str, ...]]]] = {
    "pipe_fitting": {
        "elbow": ("pipe_fitting_elbows.json", ElbowGenerator,
                  ("outer_diameter", "wall_thickness", "bend_radius")),
        "tee": ("pipe_fitting_tees.json", TeeGenerator,
                ("outer_diameter", "wall_thickness", "run_length", "branch_length")),
        "reducer": ("pipe_fitting_reducers.json", ReducerGenerator,
                    ("large_diameter", "small_diameter", "wall_thickness", "length")),
    },
}


class StandardLibrary:
    """Generates standard-part documents by family (+ optional subtype) + designation."""

    def families(self) -> list[str]:
        """The standard-part families this library can generate (flat + grouped)."""
        return sorted([*_FAMILIES.keys(), *_SUBTYPED_FAMILIES.keys()])

    def subtypes(self, family: str) -> list[str]:
        """The subtypes of a grouped ``family`` (pipe_fitting -> elbow/tee/reducer); else []."""
        return sorted(_SUBTYPED_FAMILIES.get(family, {}).keys())

    def designations(self, family: str, subtype: str | None = None) -> list[str]:
        """The designation keys available for ``family`` (+ ``subtype`` for a grouped family)."""
        return self._table(family, subtype).designations()

    def required_dimensions(self, family: str, subtype: str | None = None) -> tuple[str, ...]:
        """The dimension keys ``family`` (+ ``subtype``) needs (for the custom path + help text)."""
        return self._entry(family, subtype)[2]

    def generate(self, family: str, designation: str, part_name: str | None = None,
                 subtype: str | None = None) -> dict:
        """Return a one-part ncad document for ``family``/``designation`` (table lookup).

        For a grouped family, pass ``subtype`` (e.g. ``pipe_fitting`` + ``elbow``). ``part_name``
        defaults to ``<family>_<subtype>_<designation>`` lowercased.
        """
        table_file, _, _ = self._entry(family, subtype)
        dimensions = StandardTable(table_file).dimensions(designation)
        name = part_name or self._default_name(family, subtype, designation)
        return self._build_document(family, subtype, name, dimensions)

    def generate_custom(self, family: str, dimensions: dict, part_name: str | None = None,
                        subtype: str | None = None) -> dict:
        """Return a one-part doc for ``family`` (+ ``subtype``) from CALLER-supplied dimensions.

        ``dimensions`` must carry every key in ``required_dimensions(family, subtype)``; a missing
        key raises ValueError. ``part_name`` defaults to ``<family>[_<subtype>]_custom``.
        """
        required = self.required_dimensions(family, subtype)
        missing = [k for k in required if k not in dimensions]
        if missing:
            raise ValueError(
                f"custom {family} needs dimensions {list(required)}; missing {missing}")
        name = part_name or self._default_name(family, subtype, "custom")
        return self._build_document(family, subtype, name, dimensions)

    def provenance(self, family: str, subtype: str | None = None) -> dict[str, str]:
        """The standard/version/source for ``family`` (+ ``subtype``), for a report or sidecar."""
        table = self._table(family, subtype)
        return {"standard": table.standard, "version": table.version, "source": table.source}

    def _default_name(self, family: str, subtype: str | None, designation: str) -> str:
        """The default part name: ``family[_subtype]_designation`` lowercased."""
        parts = [family, subtype, designation] if subtype else [family, designation]
        return "_".join(parts).lower()

    def _build_document(self, family: str, subtype: str | None, part_name: str,
                        dimensions: dict) -> dict:
        """Run the ``family`` (+ ``subtype``) generator over ``dimensions`` into a part document."""
        _, generator_factory, _ = self._entry(family, subtype)
        return generator_factory().generate(part_name, dimensions)

    def _entry(self, family: str,
               subtype: str | None) -> tuple[str, Callable[[], Any], tuple[str, ...]]:
        """The registry entry for a flat family or a grouped ``family`` + ``subtype``.

        Raises KeyError with the known keys when the family/subtype is unknown, or when a subtype
        is required but missing (or given for a flat family).
        """
        if family in _SUBTYPED_FAMILIES:
            subtypes = _SUBTYPED_FAMILIES[family]
            if subtype is None:
                raise KeyError(
                    f"{family!r} needs a subtype; known: {sorted(subtypes.keys())}")
            if subtype not in subtypes:
                raise KeyError(
                    f"unknown {family} subtype {subtype!r}; known: {sorted(subtypes.keys())}")
            return subtypes[subtype]
        if family not in _FAMILIES:
            raise KeyError(
                f"unknown standard-part family {family!r}; "
                f"known: {sorted([*_FAMILIES, *_SUBTYPED_FAMILIES])}")
        if subtype is not None:
            raise KeyError(f"family {family!r} takes no subtype (got {subtype!r})")
        return _FAMILIES[family]

    def _table(self, family: str, subtype: str | None = None) -> StandardTable:
        """The loaded StandardTable for ``family`` (+ ``subtype``)."""
        return StandardTable(self._entry(family, subtype)[0])
