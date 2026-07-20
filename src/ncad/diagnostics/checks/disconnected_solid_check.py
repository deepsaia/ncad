"""Report (info) when a part builds as multiple disjoint solids.

A part that comes out as several separate lumps is often the "floating bodies" authoring bug (a
feature placed where it does not touch its neighbors, e.g. a stand whose base does not reach its
posts). But disjoint solids are also LEGITIMATE - a deliberate multibody part, a pattern/mirror with
merge=false, a split. Intent expressed purely through geometry cannot be told apart from the bug, so
this check makes NO judgment: it simply emits an INFO diagnostic with the body count whenever a part
has more than one disjoint solid, surfacing the fact for the author (and saving a hand-rolled body
count). Info severity never blocks the build. One class.
"""

from ncad.diagnostics import codes
from ncad.diagnostics.diagnostic import Diagnostic


class DisconnectedSolidCheck:
    """Emits an info diagnostic reporting a part's disjoint-solid count when it is more than one."""

    def check(self, part_name: str, body_count: int) -> list[Diagnostic]:
        """Return an info Diagnostic when ``body_count`` > 1, else nothing."""
        if body_count <= 1:
            return []
        return [Diagnostic(
            severity="info", code=codes.DISCONNECTED_SOLID,
            location=f"parts.{part_name}",
            message=f"part {part_name!r} built as {body_count} disjoint solids",
            hint="expected for a multibody part (pattern/mirror merge=false, split); if it should "
                 "be one connected solid, a feature may not touch its neighbors (floating bodies)",
            stage="build")]
