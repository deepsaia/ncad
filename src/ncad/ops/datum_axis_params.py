"""Parse and validate a datum_axis feature's construction method + args.

A datum axis is built by one of: ``two_point`` (through two ``datum_points``), ``edge``
(along an edge reference), ``intersection`` (of two datum planes in the refs), or
``normal_to_face`` (a face normal at a point). This matches the NX/Creo/Fusion datum-axis
methods. A contract violation raises DatumAxisParamError (the op wraps it into an id-tagged
issue). The kernel returns the axis as an ``((ox,oy,oz), (dx,dy,dz))`` tuple, the same axis
shape ``revolve`` consumes.
"""

_METHODS = ("two_point", "edge", "intersection", "normal_to_face")


class DatumAxisParamError(Exception):
    """A datum_axis method or its arguments are missing or malformed."""


def datum_axis_kwargs(params: dict, refs: dict) -> dict:
    """Normalize a datum_axis feature dict into kernel kwargs."""
    method = params.get("method")
    if method not in _METHODS:
        raise DatumAxisParamError(
            f"datum_axis needs a method in {_METHODS}; got {method!r}")
    if method == "two_point":
        points = params.get("datum_points", [])
        if len(points) != 2:
            raise DatumAxisParamError("datum_axis two_point needs exactly 2 datum_points")
        return {"method": "two_point",
                "points": [tuple(float(c) for c in p) for p in points]}
    if method == "normal_to_face":
        at = params.get("at_point")
        return {"method": "normal_to_face",
                "at_point": tuple(float(c) for c in at) if at is not None else None}
    # edge / intersection carry their geometry via refs (edge handle / two plane refs).
    return {"method": method}
