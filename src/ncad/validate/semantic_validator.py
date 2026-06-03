"""Orchestrates the semantic validators into a single pass over a spec.

Runs the geometric, topological, and architectural validators and concatenates their
issues. Returns issues as data (design.md §5); raising is reserved for contract errors,
not validation findings.
"""

import logging

from ncad.validate.architectural_validator import ArchitecturalValidator
from ncad.validate.geometry_validator import GeometryValidator
from ncad.validate.issue import Issue
from ncad.validate.loop_validator import LoopValidator
from ncad.validate.topology_validator import TopologyValidator

logger = logging.getLogger(__name__)


class SemanticValidator:
    """Runs all semantic validators and aggregates their issues."""

    def __init__(self) -> None:
        self._validators = [
            GeometryValidator(),
            TopologyValidator(),
            ArchitecturalValidator(),
            LoopValidator(),
        ]

    def validate(self, spec: dict) -> list[Issue]:
        """Return all semantic issues for ``spec`` (empty if clean)."""
        issues: list[Issue] = []
        for validator in self._validators:
            issues.extend(validator.validate(spec))
        if issues:
            logger.debug("spec has %d semantic issue(s)", len(issues))
        return issues
