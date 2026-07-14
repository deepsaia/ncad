"""Parse and validate a ``mirror`` feature's vocabulary into a placement description.

A mirror reflects the running body/bodies across a plane (see plane_spec for the plane
vocabulary). ``keep`` (default true) keeps the original and adds the reflected copy;
``merge`` (default true) fuses the two to one solid. A contract violation raises
MirrorParamError (the op wraps it into a BuildIssue).
"""

import logging

from ncad.ops.plane_spec import PlaneSpecError, parse_plane

logger = logging.getLogger(__name__)


class MirrorParamError(Exception):
    """A mirror's plane/keep/merge vocabulary is missing or invalid."""


def mirror_kwargs(params: dict, refs: dict | None = None) -> dict:
    """Return the validated mirror description: plane (normalized), keep, merge.

    The mirror plane is a base string / {point, normal} object (``plane``), OR a referenced
    planar FACE (``refs["face"]``): the face's center + normal become a custom plane. A
    non-planar face is refused (a mirror plane must be planar).
    """
    refs = refs or {}
    face = refs.get("face")
    if face is not None:
        plane = _plane_from_face(face)
    else:
        if "plane" not in params:
            raise MirrorParamError(
                "mirror needs a 'plane' (XY/XZ/YZ, {point, normal}, or a face reference)")
        try:
            plane = parse_plane(params["plane"], params.get("plane_offset", 0.0))
        except PlaneSpecError as exc:
            raise MirrorParamError(str(exc)) from exc
    return {"plane": plane,
            "keep": bool(params.get("keep", True)),
            "merge": bool(params.get("merge", True))}


def _plane_from_face(face) -> dict:
    """A custom {point, normal} plane from a planar face's center + normal; else refuse."""
    geom = getattr(face, "geom_type", None)
    name = getattr(geom, "name", geom)   # a GeomType enum has .name; a stub gives a string
    if str(name).upper() != "PLANE":
        raise MirrorParamError(f"mirror across a face needs a PLANAR face; got a {name} face")
    center = face.center()
    try:
        normal = face.normal_at(center)
    except TypeError:
        normal = face.normal_at()
    return {"kind": "custom",
            "point": (center.X, center.Y, center.Z),
            "z_dir": (normal.X, normal.Y, normal.Z)}
