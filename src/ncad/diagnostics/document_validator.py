"""Validate an ncad document (part / assembly / motion) into a single ValidationReport.

The unified static-validation entry point (agent-facing): detects the document kind and runs the
applicable schema + semantic checks, returning coded Diagnostics. NEVER raises for a bad design; an
exception is reserved for a true programmer/contract error. No geometry (no kernel): fast +
side-effect-free. Referenced part connector sets and a motion's assembly are resolved from base_dir
(best-effort; an unreadable file becomes a diagnostic, not an exception). One class.
"""

import logging
import os

from ncad.build.material_error import MaterialError
from ncad.diagnostics import codes
from ncad.diagnostics.checks.assembly_reference_check import AssemblyReferenceCheck
from ncad.diagnostics.checks.material_reference_check import MaterialReferenceCheck
from ncad.diagnostics.checks.motion_reference_check import MotionReferenceCheck
from ncad.diagnostics.diagnostic import Diagnostic
from ncad.diagnostics.validation_report import ValidationReport
from ncad.spec.assembly_schema_validator import AssemblySchemaValidator
from ncad.spec.dependency_validator import DependencyValidator
from ncad.spec.feature_id_validator import FeatureIdValidator
from ncad.spec.material_library import MaterialLibrary
from ncad.spec.schema_issue import SchemaIssue
from ncad.spec.schema_validator import SchemaValidator
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)


class DocumentValidator:
    """Runs schema + semantic checks for any ncad document kind, returning one ValidationReport."""

    def __init__(self, base_dir: str = "") -> None:
        self._base_dir = base_dir
        self._loader = SpecLoader()
        self._schema = SchemaValidator()
        self._asm_schema = AssemblySchemaValidator()
        self._ids = FeatureIdValidator()
        self._deps = DependencyValidator()
        self._asm_refs = AssemblyReferenceCheck()
        self._motion_refs = MotionReferenceCheck()
        self._material_refs = MaterialReferenceCheck()

    def validate(self, document: dict) -> ValidationReport:
        """Detect the kind and return its ValidationReport (never raises for a bad design)."""
        if "motion" in document:
            return ValidationReport(self._validate_motion(document))
        if "assembly" in document:
            return ValidationReport(self._validate_assembly(document))
        return ValidationReport(self._validate_part(document))

    def _validate_part(self, document: dict) -> list[Diagnostic]:
        out = [i.to_diagnostic("schema", codes.SCHEMA) for i in self._schema.validate(document)]
        out += [i.to_diagnostic("semantic", codes.DUPLICATE_ID)
                for i in self._ids.validate(document)]
        out += [i.to_diagnostic("semantic", self._dep_code(i))
                for i in self._deps.validate(document)]
        known = self._known_materials(document)
        if known is not None:
            out += self._material_refs.check(document, known)
        return out

    def _known_materials(self, document: dict) -> set | None:
        """The resolvable material names (seed + inline + external), or None to SKIP the check.

        Covers a user's own inline ``materials {}`` and an external ``materials_library`` file
        (both merged by MaterialLibrary onto the seed). Returns None - so the material-reference
        check does NOT run and cannot false-flag - when the library cannot be fully resolved: an
        external library referenced but unreadable (no base_dir, missing file, bad record).
        Skipping is the safe choice: better to miss a typo than to flag every material as unknown.
        """
        if document.get("materials_library") and not self._base_dir:
            return None
        try:
            return MaterialLibrary(document, base_dir=self._base_dir or None).names()
        except (MaterialError, ValueError, OSError) as exc:
            logger.debug("material library unresolved; skipping material-reference check: %s", exc)
            return None

    def _validate_assembly(self, document: dict) -> list[Diagnostic]:
        out = [i.to_diagnostic("schema", codes.SCHEMA)
               for i in self._asm_schema.validate(document)]
        connectors = self._connectors_for(document.get("assembly") or {})
        out += self._asm_refs.check(document, connectors)
        return out

    def _validate_motion(self, document: dict) -> list[Diagnostic]:
        motion = document.get("motion") or {}
        asm_doc = self._load_relative(motion.get("assembly"))
        asm_block = (asm_doc or {}).get("assembly") if asm_doc else None
        out: list[Diagnostic] = []
        if asm_block is not None:
            connectors = self._connectors_for(asm_block)
            out += self._asm_refs.check({"assembly": asm_block}, connectors)
        out += self._motion_refs.check(document, asm_block)
        return out

    def _connectors_for(self, assembly: dict) -> dict:
        """Map each referenced part name -> its declared connector-id set (best-effort by file)."""
        connectors: dict = {}
        for inst in assembly.get("instances") or []:
            part_doc = self._load_relative(inst.get("file"))
            if part_doc is None:
                continue
            for part_name, part in (part_doc.get("parts") or {}).items():
                connectors[part_name] = {c.get("id") for c in (part.get("connectors") or [])}
        return connectors

    def _load_relative(self, ref: str | None) -> dict | None:
        """Load a referenced doc relative to base_dir; None if absent/unreadable (a diagnostic)."""
        if not ref or not self._base_dir:
            return None
        path = os.path.join(self._base_dir, ref)
        if not os.path.isfile(path):
            return None
        try:
            return self._loader.load(path)
        except (ValueError, OSError) as exc:
            logger.debug("validator could not load %s: %s", path, exc)
            return None

    def _dep_code(self, issue: SchemaIssue) -> str:
        """Dependency-validator issues carry the kind in the message ('defined later' = forward)."""
        if "defined later" in issue.message:
            return codes.FORWARD_REFERENCE
        return codes.UNKNOWN_REFERENCE
