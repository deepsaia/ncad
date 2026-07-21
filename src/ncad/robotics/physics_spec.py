"""Parse a ``.physics.hocon`` overlay: the robot/sim semantics layered on top of an assembly.

A physics document is an OVERLAY, not a standalone robot: it references an assembly (which supplies
the links, joints, frames, and computed inertia) and adds only what the assembly does not know:
which joints are actuated, their limits/dynamics, the base (root) link, and the export target. This
mirrors how a ``.motion.hocon`` overlays an assembly with a driver. This class validates the
overlay into a queryable spec; geometry/inertia are never authored here (they are derived).

Document shape::

    physics {
      assembly = arm.asm.hocon
      base = link0
      joints { j1 { actuated = true, limit = [-3.14, 3.14], effort = 50, velocity = 2.0,
                    damping = 0.1, friction = 0.0 } }
      export { format = urdf, mesh = stl }
    }
"""

_FORMATS = frozenset({"urdf"})   # MJCF/SDF land as follow-up writers on the same IR


class PhysicsSpecError(Exception):
    """A physics overlay is missing its assembly reference or has an invalid export format."""


class PhysicsSpec:
    """A validated ``.physics.hocon`` overlay: assembly ref, base, per-joint semantics, export."""

    def __init__(self, document: dict) -> None:
        physics = document.get("physics")
        if not isinstance(physics, dict):
            raise PhysicsSpecError("physics document needs a top-level 'physics' block")
        if not physics.get("assembly"):
            raise PhysicsSpecError("physics overlay needs an 'assembly' reference")
        self._physics = physics
        export = physics.get("export") or {}
        fmt = str(export.get("format", "urdf"))
        if fmt not in _FORMATS:
            raise PhysicsSpecError(
                f"unsupported export format {fmt!r}; supported: {sorted(_FORMATS)}")
        self._format = fmt

    @property
    def assembly(self) -> str:
        """The referenced assembly document path (relative to the physics doc)."""
        return str(self._physics["assembly"])

    @property
    def base_link(self) -> str | None:
        """The authored base (root) link instance id, or None to auto-pick a grounded/first link."""
        base = self._physics.get("base")
        return str(base) if base else None

    @property
    def export_format(self) -> str:
        """The export target format (``urdf`` today)."""
        return self._format

    @property
    def mesh_format(self) -> str:
        """The per-link mesh format for visual/collision geometry (default ``stl``)."""
        return str((self._physics.get("export") or {}).get("mesh", "stl"))

    def joint_overlay(self, joint_id: str) -> dict:
        """The authored semantics for ``joint_id`` (actuated/limit/effort/...); empty if none."""
        return dict((self._physics.get("joints") or {}).get(joint_id, {}))
