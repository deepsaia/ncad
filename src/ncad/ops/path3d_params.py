"""Parse and validate a ``path3d`` feature's vocabulary into a 3D-wire description.

A ``path3d`` is a free space curve used as a sweep path (a centerline that turns in all three axes,
unlike a planar open sketch). It names ordered ``points`` (each ``[x, y, z]``) and a ``kind``:
``polyline`` (straight segments) or ``spline`` (a smooth curve through every point); ``closed``
joins the last point back to the first. This turns the authored vocabulary into a validated
description; the op calls ``kernel.wire3d``. A contract violation raises Path3dParamError (the op
wraps it into a BuildIssue).
"""

_KINDS = frozenset({"polyline", "spline"})


class Path3dParamError(Exception):
    """A path3d points list, point shape, or kind is invalid."""


def path3d_kwargs(params: dict) -> dict:
    """Return the validated 3D-path description ``{points, kind, closed}`` for a path3d feature."""
    kind = str(params.get("kind", "polyline"))
    if kind not in _KINDS:
        raise Path3dParamError(f"unknown path3d kind {kind!r}; expected {sorted(_KINDS)}")
    raw_points = params.get("points")
    if not isinstance(raw_points, (list, tuple)) or len(raw_points) < 2:
        raise Path3dParamError("path3d needs a 'points' list of at least 2 [x, y, z] points")
    points: list[tuple[float, float, float]] = []
    for point in raw_points:
        if not isinstance(point, (list, tuple)) or len(point) != 3:
            raise Path3dParamError(f"path3d point must be [x, y, z]; got {point!r}")
        points.append((float(point[0]), float(point[1]), float(point[2])))
    closed = bool(params.get("closed", False))
    if kind == "spline" and len(points) + (1 if closed else 0) < 3:
        raise Path3dParamError("path3d spline needs at least 3 points (2 if closed)")
    return {"points": points, "kind": kind, "closed": closed}
