"""A single schema-validation issue, returned as data rather than raised."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaIssue:
    """One schema violation found in a spec.

    :ivar location: Dotted/indexed path to the offending field (e.g.
        ``storeys.0.walls.0.thickness``), or ``"<root>"`` for top-level issues.
    :ivar message: Human-readable description of the violation.
    """

    location: str
    message: str
