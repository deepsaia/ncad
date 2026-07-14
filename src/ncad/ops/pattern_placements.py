"""Pure placement math for the ``pattern`` op: kwargs -> ordered transform specs.

Given a validated ``pattern_kwargs`` dict, produce one transform-kwargs dict per instance
in generation order. Index 0 is always the identity placement ({}), the seed. This module
does NOT import the kernel or build123d: it computes placements analytically (plain trig),
which keeps it FakeKernel-safe, unit-testable in isolation, and free to support arbitrary
linear directions and rotation axes (unlike build123d GridLocations/PolarLocations, which
are axis-locked). The op splats each returned dict into ``kernel.transform``.
"""

import logging
import math

logger = logging.getLogger(__name__)


class PatternPlacements:
    """Turns a validated pattern description into ordered per-instance transform specs."""

    def __init__(self, kwargs: dict,
                 anchor: tuple[float, float, float] | None = None) -> None:
        self._kwargs = kwargs
        self._anchor = anchor

    def specs(self) -> list[dict]:
        """Ordered transform-kwargs, one per instance; index 0 is identity ({})."""
        kind = self._kwargs["kind"]
        if kind == "linear":
            return self._linear_specs(self._kwargs["linear"])
        if kind == "circular":
            return self._circular_specs(self._kwargs["circular"])
        if kind == "table":
            return self._table_specs(self._kwargs["table"])
        return self._curve_specs(self._kwargs["curve"])

    def _table_specs(self, rows: list[dict]) -> list[dict]:
        """One spec per explicit placement row: move to ``at``, optional +Z rotate."""
        specs: list[dict] = []
        for row in rows:
            at = row["at"]
            spec: dict = {} if at == (0.0, 0.0, 0.0) else {"move": at}
            if "rotate" in row:
                spec["rotate"] = {"axis": (0.0, 0.0, 1.0), "angle": row["rotate"],
                                  "about": at}
            specs.append(spec)
        return specs

    def _curve_specs(self, spec: dict) -> list[dict]:
        """Move each instance from the seed (first sampled point) to its sampled point.

        Positions are the core path-pattern behavior; tangent-align is a follow-up (it needs a
        rotate-between-tangents transform).
        """
        points = spec["points"]
        seed = points[0]
        specs: list[dict] = []
        for i, point in enumerate(points):
            move = _sub(point, seed)
            specs.append({} if (i == 0 or move == (0.0, 0.0, 0.0)) else {"move": move})
        return specs

    def _linear_specs(self, spec: dict) -> list[dict]:
        """Row-major grid: ordinal = iy*count_x + ix; move sums the two axis steps."""
        x = spec["x"]
        y = spec["y"]
        count_y = y["count"] if y is not None else 1
        specs: list[dict] = []
        for iy in range(count_y):
            for ix in range(x["count"]):
                move = _add(_scale(x["dir"], ix * x["spacing"]),
                            _scale(y["dir"], iy * y["spacing"]) if y is not None
                            else (0.0, 0.0, 0.0))
                # Ordinal 0 (ix=iy=0) lands on the origin: emit {} so the op leaves the seed
                # body untouched (instance 0 is geometrically exact, not a transformed copy).
                specs.append({} if move == (0.0, 0.0, 0.0) else {"move": move})
        return specs

    def _circular_specs(self, spec: dict) -> list[dict]:
        """Polar array: rotate=true rotates about the axis; rotate=false translates."""
        count = spec["count"]
        step = _step_angle(spec["angle"], count)
        axis = spec["axis"]
        specs: list[dict] = []
        for k in range(count):
            if k == 0:
                specs.append({})   # seed = identity (instance 0)
                continue
            angle = k * step
            if spec["rotate"]:
                # A single rotation about the axis both places the instance on the arc and
                # orients it tangentially (the exact bolt-circle behavior).
                specs.append({"rotate": {"axis": axis["dir"], "angle": angle,
                                         "about": axis["point"]}})
            else:
                # Translate-only: move the source from its anchor to where a rotation would
                # carry it, without reorienting it. Needs the anchor (op supplies bbox center).
                if self._anchor is None:
                    raise ValueError(
                        "circular pattern rotate=false needs an anchor point")
                rotated = _rotate_point(self._anchor, axis["point"], axis["dir"], angle)
                specs.append({"move": _sub(rotated, self._anchor)})
        return specs


def _step_angle(angle: float, count: int) -> float:
    """Degrees between adjacent instances.

    A full circle (360) divides by count so the endpoint is not duplicated; a partial arc
    divides by count-1 so both ends are hit. count == 1 yields the seed only (step unused).
    """
    if count <= 1:
        return 0.0
    if angle == 360.0:
        return angle / count
    return angle / (count - 1)


def _add(a: tuple[float, float, float], b: tuple[float, float, float]
         ) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: tuple[float, float, float], b: tuple[float, float, float]
         ) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(v: tuple[float, float, float], k: float) -> tuple[float, float, float]:
    return (v[0] * k, v[1] * k, v[2] * k)


def _rotate_point(point: tuple[float, float, float], about: tuple[float, float, float],
                  axis_dir: tuple[float, float, float], angle_deg: float
                  ) -> tuple[float, float, float]:
    """Rodrigues rotation of ``point`` about the line through ``about`` along ``axis_dir``."""
    length = math.sqrt(axis_dir[0] ** 2 + axis_dir[1] ** 2 + axis_dir[2] ** 2)
    ux, uy, uz = axis_dir[0] / length, axis_dir[1] / length, axis_dir[2] / length
    px, py, pz = point[0] - about[0], point[1] - about[1], point[2] - about[2]
    theta = math.radians(angle_deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    dot = ux * px + uy * py + uz * pz
    cross = (uy * pz - uz * py, uz * px - ux * pz, ux * py - uy * px)
    rx = px * cos_t + cross[0] * sin_t + ux * dot * (1 - cos_t)
    ry = py * cos_t + cross[1] * sin_t + uy * dot * (1 - cos_t)
    rz = pz * cos_t + cross[2] * sin_t + uz * dot * (1 - cos_t)
    return (rx + about[0], ry + about[1], rz + about[2])
