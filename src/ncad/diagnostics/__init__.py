"""Unified validation & diagnostics: the agent-facing issue contract."""

# `Diagnostic`/`DiagnosticError` are leaf types (no ncad imports), so they are re-exported eagerly.
# `DocumentValidator`/`ValidationReport` pull in the schema validators, which import
# ncad.spec.schema_issue, which imports THIS package for `Diagnostic` - an import-time cycle. They
# are therefore exposed LAZILY via module __getattr__ (PEP 562): the name resolves on first access,
# after this package has finished initializing, so `from ncad.diagnostics import Diagnostic` (the
# path schema_issue takes) no longer drags the validators in mid-init. Same public API, no cycle.
from typing import Any

from ncad.diagnostics.diagnostic import Diagnostic, DiagnosticError

__all__ = ["Diagnostic", "DiagnosticError", "DocumentValidator", "ValidationReport"]

_LAZY = {
    "DocumentValidator": "ncad.diagnostics.document_validator",
    "ValidationReport": "ncad.diagnostics.validation_report",
}


def __getattr__(name: str) -> Any:
    """Lazily import the heavy validators on first access (breaks the schema_issue import cycle)."""
    module_path = _LAZY.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib
    return getattr(importlib.import_module(module_path), name)
