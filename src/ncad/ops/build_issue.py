"""A single build-time issue, returned as data rather than raised (design §10)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuildIssue:
    """One problem encountered while building a feature, tagged by node id.

    :ivar node_id: The ``id`` of the feature/node the issue is attributed to.
    :ivar message: Human-readable description of the problem.
    """

    node_id: str
    message: str
