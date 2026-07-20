"""Unified validation & diagnostics: the agent-facing issue contract."""

from ncad.diagnostics.diagnostic import Diagnostic, DiagnosticError
from ncad.diagnostics.document_validator import DocumentValidator
from ncad.diagnostics.validation_report import ValidationReport

__all__ = ["Diagnostic", "DiagnosticError", "DocumentValidator", "ValidationReport"]
