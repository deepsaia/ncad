"""The pure feature executor: builds a document's parts into geometry."""

# Builder/DocumentBuilder are exposed LAZILY (PEP 562): eagerly importing DocumentBuilder here pulls
# ncad.build.material_resolver -> ncad.spec.material_library -> ncad.build.material_error, which
# re-enters this package mid-init (an import cycle). Deferring the import to first attribute access
# lets a leaf like ncad.build.material_error be imported without dragging the whole executor in.
from typing import Any

__all__ = ["Builder", "DocumentBuilder"]

_LAZY = {
    "Builder": "ncad.build.builder",
    "DocumentBuilder": "ncad.build.document_builder",
}


def __getattr__(name: str) -> Any:
    """Lazily import Builder/DocumentBuilder on first access (breaks the material import cycle)."""
    module_path = _LAZY.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib
    return getattr(importlib.import_module(module_path), name)
