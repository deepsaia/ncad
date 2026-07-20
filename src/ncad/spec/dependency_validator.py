"""Pre-build semantic check: named references must exist and be defined earlier.

A feature's structural references (profile / target / tool) must name another feature
in the same part that is defined before it in the authored order. A forward reference
or a reference to a missing id is a contract error, reported by the offending feature
id before any geometry runs. Generative/selector references (``on``,
``edges``) are not checked here: they resolve against live topology at build time and
are the reference model's job to fail loudly.
"""

import logging

from ncad.spec.schema_issue import SchemaIssue

logger = logging.getLogger(__name__)

# Reference fields that name another feature by id (mirrors the RebuildGraph deps).
_NAMED_REF_FIELDS = ("profile", "target", "tool")


class DependencyValidator:
    """Reports structural references that are unknown or defined later."""

    def validate(self, spec: dict) -> list[SchemaIssue]:
        """Return one issue per unknown or forward named reference, scoped per part."""
        issues: list[SchemaIssue] = []
        for part_name, part in spec.get("parts", {}).items():
            features = part.get("features", [])
            all_ids = {f.get("id") for f in features}
            seen: set = set()
            location = f"parts.{part_name}.features"
            for feature in features:
                fid = feature.get("id")
                for field in _NAMED_REF_FIELDS:
                    ref = feature.get(field)
                    if not isinstance(ref, str) or not ref:
                        continue
                    if ref not in all_ids:
                        issues.append(SchemaIssue(
                            location=location,
                            message=f"{fid} references unknown feature {ref!r}"))
                    elif ref not in seen:
                        issues.append(SchemaIssue(
                            location=location,
                            message=f"{fid} references {ref!r} defined later"))
                if fid is not None:
                    seen.add(fid)
        return issues
