"""Load, validate, and resolve materials from the seed + document-inline + external library.

A material record (`mat_data`) is an open, grouped property bag (physical/structural/thermal/
appearance + custom keys). Materials are authored in HOCON: a built-in seed ships in
``materials/seed.hocon``; a document may add/override via an inline ``materials {}`` block
and/or an external ``materials_library = "..."`` file. Lookup precedence is
document-inline > external file > seed. Density is in kg/m^3 (see MassCalculator for the
mass unit convention). This layer is document data, never the geometry kernel.
"""

import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ncad.build.material_error import MaterialError
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_SEED_PATH = Path(__file__).resolve().parents[3] / "materials" / "seed.hocon"
_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "materials_schema.hocon"


class MaterialLibrary:
    """A resolvable set of materials merged from seed, external file, and document-inline."""

    def __init__(self, document: dict, base_dir: str | None = None) -> None:
        loader = SpecLoader()
        self._validator = Draft202012Validator(loader.load(str(_SCHEMA_PATH)))
        # Precedence is applied by merge order: seed first, then external, then inline last so
        # inline wins. Each layer is a name -> record map.
        merged: dict = dict(loader.load(str(_SEED_PATH)))
        external = document.get("materials_library")
        if external is not None:
            path = Path(external)
            if base_dir is not None and not path.is_absolute():
                path = Path(base_dir) / path
            _merge_layer(merged, loader.load(str(path)))
        _merge_layer(merged, document.get("materials", {}))
        for name, record in merged.items():
            self._validate(name, record)
        self._materials = merged

    def has(self, name: str) -> bool:
        """Whether ``name`` resolves to a material."""
        return name in self._materials

    def names(self) -> set:
        """The set of all resolvable material names (seed + external + document-inline)."""
        return set(self._materials)

    def resolve(self, name: str, override: dict | None = None) -> dict:
        """The merged ``mat_data`` for ``name`` (with ``override`` deep-merged on top)."""
        if name not in self._materials:
            raise MaterialError(f"unknown material {name!r}")
        record = _deep_copy(self._materials[name])
        if override:
            _deep_merge(record, override)
            self._validate(name, record)
        return record

    def _validate(self, name: str, record: dict) -> None:
        """Raise MaterialError if ``record`` fails the material schema."""
        errors = sorted(self._validator.iter_errors(record), key=str)
        if errors:
            raise MaterialError(f"material {name!r} invalid: {errors[0].message}")


def _merge_layer(base: dict, layer: dict) -> None:
    """Merge a name -> record ``layer`` onto ``base`` (record-level deep merge)."""
    for name, record in layer.items():
        if name in base and isinstance(base[name], dict) and isinstance(record, dict):
            merged = _deep_copy(base[name])
            _deep_merge(merged, record)
            base[name] = merged
        else:
            base[name] = _deep_copy(record)


def _deep_merge(base: dict, over: dict) -> None:
    """Recursively merge ``over`` into ``base`` (dicts merge; scalars/lists replace)."""
    for key, value in over.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = _deep_copy(value)


def _deep_copy(value: Any) -> Any:
    """A structural copy so merges never mutate a shared source record."""
    if isinstance(value, dict):
        return {k: _deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy(v) for v in value]
    return value
