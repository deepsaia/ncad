"""Parse and validate a datum_plane feature's construction method + args.

A datum plane is built by one of: ``offset`` (a base plane or planar face shifted by
``distance``), ``angled`` (through a base plane rotated by ``angle``), ``on_face``
(coincident with a planar face), or ``three_point`` (through 3 points). A bare ``base``
plane with a ``distance`` defaults to ``offset``. This matches the NX/Creo/Fusion
datum-plane methods. A contract violation raises DatumPlaneParamError (the op wraps it into
an id-tagged issue).
"""

_METHODS = ("offset", "angled", "on_face", "three_point")
_BASE_PLANES = ("XY", "XZ", "YZ")


class DatumPlaneParamError(Exception):
    """A datum_plane method or its arguments are missing or malformed."""


def datum_plane_kwargs(params: dict, refs: dict) -> dict:
    """Normalize a datum_plane feature dict into kernel kwargs."""
    method = params.get("method")
    if method is None and params.get("base") in _BASE_PLANES:
        method = "offset"
    if method not in _METHODS:
        raise DatumPlaneParamError(
            f"datum_plane needs a method in {_METHODS} or a base plane; got {method!r}")
    if method == "offset":
        base = params.get("base")
        if base is not None and base not in _BASE_PLANES:
            raise DatumPlaneParamError(
                f"datum_plane offset base must be a base plane (or offset a face via a "
                f"'face' reference); got {base!r}")
        return {"method": "offset", "base": base,
                "distance": float(params.get("distance", 0.0))}
    if method == "three_point":
        points = params.get("datum_points", [])
        if len(points) != 3:
            raise DatumPlaneParamError("datum_plane three_point needs exactly 3 datum_points")
        return {"method": "three_point",
                "points": [tuple(float(c) for c in p) for p in points]}
    if method == "angled":
        if "angle" not in params:
            raise DatumPlaneParamError("datum_plane angled needs an 'angle'")
        return {"method": "angled", "base": params.get("base", "XY"),
                "angle": float(params["angle"])}
    return {"method": "on_face"}  # the planar face arrives via refs["face"]
