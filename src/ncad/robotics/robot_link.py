"""A robot link in the format-neutral robot IR: a body with derived inertial + a visual mesh.

One rigid body of a robot description. Everything here is DERIVED from the built assembly, never
hand-authored: ``mass``/``inertia``/``center_of_mass`` come from ncad's MassCalculator (the B3
computed tensor), and ``mesh`` is the per-link mesh exported by the Stage-0 pipeline. A format
writer (URDF/MJCF/SDF) turns this neutral link into that format's link/body element.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RobotLink:
    """A robot link: name + derived inertial (SI kg, kg*m^2, m) + an optional visual mesh."""

    name: str
    mass: float
    # Centroidal inertia tensor as the six independent terms (kg*m^2), about the center of mass.
    inertia: dict[str, float] = field(default_factory=dict)
    # Center of mass in the link frame (metres).
    center_of_mass: tuple[float, float, float] = (0.0, 0.0, 0.0)
    # Path to the link's mesh (relative to the export dir), or None for an inertia-only link.
    mesh: str | None = None
