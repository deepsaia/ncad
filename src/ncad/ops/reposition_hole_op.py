"""The ``reposition_hole`` direct op: move a baked (history-free) hole to a new location.

The NX/Creo/Fusion "move hole" on an imported or history-free solid: there is no feature to
re-run, so the op reads the hole's cylindrical face (axis, radius, location), FILLS the old hole
by fusing a plug cylinder spanning the solid along that axis, then RE-CUTS an identical cylinder
at the target position. Purely additive booleans (fuse + cut), reusing the Task 1 tool-capture
idea (the hole cutter is a reusable cylinder tool). Distinct from the history-based ``hole`` op,
which drills into the running solid at author time.
"""

import logging
from typing import Any

from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.reposition_hole_params import RepositionHoleParamError, reposition_hole_kwargs

logger = logging.getLogger(__name__)

_AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}


class RepositionHoleOp:
    """Fills a hole identified by its cylindrical face and re-cuts it at a target position."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict, kernel: Any) -> OpResult:
        node_id = params.get("id", "reposition_hole")
        if shape_in is None:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, "reposition_hole has no input solid")])
        face = params.get("__refs__", {}).get("hole")
        if face is None:
            return OpResult(shape=None, issues=[BuildIssue(
                node_id, "reposition_hole needs a 'hole' cylindrical face reference")])
        try:
            kwargs = reposition_hole_kwargs(params)
        except RepositionHoleParamError as exc:
            return OpResult(shape=None, issues=[BuildIssue(node_id, str(exc))])
        geom = _hole_geometry(face)
        if geom is None:
            return OpResult(shape=None, issues=[BuildIssue(
                node_id, "reposition_hole 'hole' face must be cylindrical")])
        axis, radius, location = geom
        try:
            result = self._reposition(shape_in, axis, radius, location, kwargs["to"], kernel)
        except KernelOpError as exc:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, f"reposition_hole failed: {exc}")])
        if result is None or kernel.volume(result) <= 0.0:
            return OpResult(shape=None, issues=[BuildIssue(
                node_id, "reposition_hole produced a degenerate solid")])
        return OpResult(shape=result)

    def _reposition(self, solid: Any, axis: str, radius: float, location: tuple,
                    to: tuple, kernel: Any) -> Any:
        """Fill the old hole with a plug spanning the solid, then re-cut at ``to``."""
        (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(solid)
        extent = {"X": maxx - minx, "Y": maxy - miny, "Z": maxz - minz}[axis]
        base_on_axis = {"X": minx, "Y": miny, "Z": minz}[axis]
        diameter = 2.0 * radius
        old_center = _center_on(location, axis, base_on_axis)
        new_center = _center_on(_place(location, axis, to), axis, base_on_axis)
        plug = kernel.cylinder(old_center, axis, diameter, extent)
        filled = kernel.fuse([solid, plug])
        cutter = kernel.cylinder(new_center, axis, diameter, extent)
        return kernel.cut(filled, [cutter])


def _hole_geometry(face: Any) -> tuple[str, float, tuple] | None:
    """The (axis letter, radius, axis_location) of a cylindrical hole face, or None."""
    attrs = getattr(face, "attrs", None)
    if attrs is None:
        return None
    direction = attrs.get("axis_direction")
    location = attrs.get("axis_location")
    radius = attrs.get("radius")
    if direction is None or location is None or radius is None:
        return None
    axis = "XYZ"[max(range(3), key=lambda i: abs(direction[i]))]
    return axis, float(radius), tuple(location)


def _center_on(location: tuple, axis: str, base_on_axis: float) -> tuple:
    """The axis-coordinate of ``location`` replaced by the solid's base (so the tool spans it)."""
    coords = list(location)
    coords[_AXIS_INDEX[axis]] = base_on_axis
    return tuple(coords)


def _place(location: tuple, axis: str, to: tuple) -> tuple:
    """``location`` with its two in-plane coordinates set to the ``to`` target (u, v)."""
    coords = list(location)
    in_plane = [i for i in range(3) if i != _AXIS_INDEX[axis]]
    coords[in_plane[0]] = to[0]
    coords[in_plane[1]] = to[1]
    return tuple(coords)
