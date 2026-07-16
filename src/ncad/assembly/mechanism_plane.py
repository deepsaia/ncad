"""The 2D plane a planar mechanism lives in, plus projection to 2D and the lift back to a 3D pose.

A planar mechanism's revolute axes are all parallel (the plane normal); its motion is a rigid body
motion IN that plane. This holds the plane basis (origin p0 + in-plane axes e1, e2 + normal n) so
the motion solver can (1) PROJECT each connector's world point to 2D (u, v) and (2) LIFT a solved 2D
delta pose (translate tdx, tdy + rotate theta about n) back to a row-major 4x4 that composes with a
body's rest placement. Pure vector math (no kernel, no solver).
"""

import math

Vec = tuple[float, float, float]


class MechanismPlane:
    """A plane (origin + orthonormal e1/e2/normal) with 2D projection and a 3D delta lift."""

    def __init__(self, origin: Vec, e1: Vec, e2: Vec, normal: Vec) -> None:
        self.origin = origin
        self.e1 = e1
        self.e2 = e2
        self.normal = normal

    @classmethod
    def from_axis_point(cls, point: Vec, axis: Vec) -> "MechanismPlane":
        """Build a plane through ``point`` with normal ``axis`` and a stable in-plane e1/e2."""
        n = _unit((float(axis[0]), float(axis[1]), float(axis[2])))
        seed = (1.0, 0.0, 0.0)
        e1 = _sub(seed, _scale(n, _dot(seed, n)))
        if _norm(e1) < 1e-9:
            seed = (0.0, 1.0, 0.0)
            e1 = _sub(seed, _scale(n, _dot(seed, n)))
        e1 = _unit(e1)
        e2 = _cross(n, e1)
        return cls((float(point[0]), float(point[1]), float(point[2])), e1, e2, n)

    def to_2d(self, world: Vec) -> tuple[float, float]:
        """Project a world point onto the plane's (e1, e2) coordinates."""
        d = _sub((float(world[0]), float(world[1]), float(world[2])), self.origin)
        return (_dot(d, self.e1), _dot(d, self.e2))

    def delta_matrix(self, theta: float, tdx: float, tdy: float) -> list[list[float]]:
        """Row-major 4x4 in-plane delta: rotate ``theta`` about n through p0, then +(tdx,tdy).

        Q' = R_n(theta) . (Q - p0) + p0 + e1*tdx + e2*tdy. Row-major so world' = world . M (the
        AssemblyPlacement convention): M[0:3][0:3] = R^T, M[3] = b = p0 - R.p0 + e1*tdx + e2*tdy.
        """
        r = _rot_about(self.normal, theta)
        shift = _add(_add(self.origin, _scale(self.e1, tdx)), _scale(self.e2, tdy))
        b = _sub(shift, _matvec(r, self.origin))
        return [[r[0][0], r[1][0], r[2][0], 0.0],
                [r[0][1], r[1][1], r[2][1], 0.0],
                [r[0][2], r[1][2], r[2][2], 0.0],
                [b[0], b[1], b[2], 1.0]]


def _rot_about(n: Vec, theta: float) -> list[list[float]]:
    """3x3 rotation (column convention) by ``theta`` about unit axis ``n`` (Rodrigues)."""
    c, s = math.cos(theta), math.sin(theta)
    nx, ny, nz = n
    return [
        [c + nx * nx * (1 - c), nx * ny * (1 - c) - nz * s, nx * nz * (1 - c) + ny * s],
        [ny * nx * (1 - c) + nz * s, c + ny * ny * (1 - c), ny * nz * (1 - c) - nx * s],
        [nz * nx * (1 - c) - ny * s, nz * ny * (1 - c) + nx * s, c + nz * nz * (1 - c)],
    ]


def _matvec(m: list[list[float]], v: Vec) -> Vec:
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


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


def _add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
