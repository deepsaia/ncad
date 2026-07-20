"""Semantic check: feature ids must be unique within a part.

Feature ids are author-controlled and used as reference names, so a collision is a
contract error, reported by the offending id (never silently suffixed). Ids are
part-scoped: the same id in two different parts is allowed.
"""

import logging

from ncad.spec.schema_issue import SchemaIssue

logger = logging.getLogger(__name__)


class FeatureIdValidator:
    """Reports duplicate feature ids within each part."""

    def validate(self, spec: dict) -> list[SchemaIssue]:
        """Return one issue per duplicated feature id, scoped per part."""
        issues: list[SchemaIssue] = []
        for part_name, part in spec.get("parts", {}).items():
            seen: set[str] = set()
            for feature in part.get("features", []):
                feature_id = feature.get("id")
                if feature_id is None:
                    continue
                if feature_id in seen:
                    issues.append(SchemaIssue(
                        location=f"parts.{part_name}.features",
                        message=f"duplicate feature id {feature_id!r}"))
                seen.add(feature_id)
        return issues
