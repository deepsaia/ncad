"""A mate connector's resolved coordinate frame: origin + an orthonormal triad (x, y, z).

Z is the primary axis (a face normal or a cylinder axis); X is the secondary axis (a projected
world axis by default, so simple connectors stay terse); Y = Z cross X. Built from geometry so the
frame follows the part across rebuilds. Pure math (reuses no kernel); the alignment math in
FrameSnap consumes these frames.
"""

import math
from dataclasses import dataclass

Vec = tuple[float, float, float]


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a: Vec) -> float:
    return math.sqrt(_dot(a, a))


def _unit(a: Vec) -> Vec:
    n = _norm(a)
    return a if n < 1e-12 else (a[0] / n, a[1] / n, a[2] / n)


def _scale(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k, a[2] * k)


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _secondary_for(z: Vec, secondary: Vec | None) -> Vec:
    # A stable X perpendicular to Z: the given secondary projected off Z, or world +X (falling
    # back to +Y when Z is parallel to +X).
    seed = secondary if secondary is not None else (1.0, 0.0, 0.0)
    proj = _sub(seed, _scale(z, _dot(seed, z)))
    if _norm(proj) < 1e-9:
        alt = (0.0, 1.0, 0.0)
        proj = _sub(alt, _scale(z, _dot(alt, z)))
    return _unit(proj)


@dataclass
class ConnectorFrame:
    """An origin plus an orthonormal (x, y, z) triad for a mate connector.

    ``radius`` is the connector's characteristic radius when it comes from a cylinder (None
    otherwise); a tangent mate reads it (bucket 5.7).
    """

    origin: Vec
    x: Vec
    y: Vec
    z: Vec
    radius: float | None = None

    @classmethod
    def from_planar(cls, center: Vec, normal: Vec, secondary: Vec | None = None,
                    offset: list | None = None) -> "ConnectorFrame":
        """Frame for a planar face: Z = normal, origin = center (plus an optional offset)."""
        z = _unit((float(normal[0]), float(normal[1]), float(normal[2])))
        x = _secondary_for(z, secondary)
        y = _cross(z, x)
        origin = (float(center[0]), float(center[1]), float(center[2]))
        return cls(_apply_offset(origin, x, y, z, offset), x, y, z)

    @classmethod
    def from_axis(cls, location: Vec, direction: Vec, secondary: Vec | None = None,
                  offset: list | None = None, radius: float | None = None) -> "ConnectorFrame":
        """Frame for a cylinder axis: Z = axis direction, origin = axis location."""
        z = _unit((float(direction[0]), float(direction[1]), float(direction[2])))
        x = _secondary_for(z, secondary)
        y = _cross(z, x)
        origin = (float(location[0]), float(location[1]), float(location[2]))
        r = float(radius) if radius is not None else None
        return cls(_apply_offset(origin, x, y, z, offset), x, y, z, r)

    @classmethod
    def from_edge(cls, midpoint: Vec, direction: Vec, secondary: Vec | None = None,
                  offset: list | None = None) -> "ConnectorFrame":
        """Frame for an edge: Z = edge direction (tangent), origin = edge midpoint."""
        z = _unit((float(direction[0]), float(direction[1]), float(direction[2])))
        x = _secondary_for(z, secondary)
        y = _cross(z, x)
        origin = (float(midpoint[0]), float(midpoint[1]), float(midpoint[2]))
        return cls(_apply_offset(origin, x, y, z, offset), x, y, z)

    @classmethod
    def from_point(cls, location: Vec, secondary: Vec | None = None,
                   offset: list | None = None) -> "ConnectorFrame":
        """Frame for a point/vertex: origin = the point, Z = world +Z (a stable default triad)."""
        z = (0.0, 0.0, 1.0)
        x = _secondary_for(z, secondary)
        y = _cross(z, x)
        origin = (float(location[0]), float(location[1]), float(location[2]))
        return cls(_apply_offset(origin, x, y, z, offset), x, y, z)

    @classmethod
    def from_datum(cls, origin: Vec, direction: Vec, secondary: Vec | None = None,
                   offset: list | None = None) -> "ConnectorFrame":
        """Frame for a datum: Z = the datum plane normal / datum axis direction."""
        return cls.from_axis(origin, direction, secondary, offset)


def _apply_offset(origin: Vec, x: Vec, y: Vec, z: Vec, offset: list | None) -> Vec:
    if not offset:
        return origin
    dx, dy, dz = float(offset[0]), float(offset[1]), float(offset[2])
    return (origin[0] + dx * x[0] + dy * y[0] + dz * z[0],
            origin[1] + dx * x[1] + dy * y[1] + dz * z[1],
            origin[2] + dx * x[2] + dy * y[2] + dz * z[2])
