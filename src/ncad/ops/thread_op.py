"""The ``thread`` feature op: cut a modeled helical thread on the running solid.

Matches the NX/Creo/Fusion Thread feature: applied to a cylindrical stud (external) or a
bore (internal), it cuts a real helical thread. The size drives pitch + major diameter via
the hole-size table (``size``), or they are given explicitly (``major_d`` + ``pitch``). The
axis defaults to Z at the origin; give ``axis`` (X/Y/Z, {point, dir}, or a datum) to place it.
"""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.hole_sizes import HoleSizeTable
from ncad.ops.op_result import OpResult
from ncad.ops.revolve_params import RevolveParamError, resolve_axis


class ThreadOp:
    """Cuts a modeled helical thread on the running solid about an axis."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="thread has no solid to thread")])
        refs = params.get("__refs__", {})
        try:
            major_d, pitch = _thread_dims(params)
            axis_point, axis_dir = _thread_axis(params, refs)
        except (RevolveParamError, ValueError, KeyError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        if "length" not in params:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="thread needs a 'length'")])
        try:
            result = kernel.thread_cut(
                shape_in, axis_point=axis_point, axis_dir=axis_dir, major_d=major_d,
                pitch=pitch, length=float(params["length"]),
                internal=bool(params.get("internal", False)))
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])


def _thread_dims(params: dict) -> tuple[float, float]:
    """Major diameter + pitch (mm): explicit ``major_d``+``pitch``, or from ``size``."""
    if "size" in params:
        table = HoleSizeTable()
        size = str(params["size"])
        return table.major_diameter(size), table.pitch(size)
    if "major_d" in params and "pitch" in params:
        return float(params["major_d"]), float(params["pitch"])
    raise ValueError("thread needs a 'size' (e.g. M6) or 'major_d' + 'pitch'")


def _thread_axis(params: dict, refs: dict) -> tuple[tuple, tuple]:
    """The thread axis (point, unit-dir): a resolved datum axis, an axis spec, or Z."""
    resolved = refs.get("axis")
    if resolved is not None:
        return resolved
    if "axis" in params:
        return resolve_axis(params["axis"])
    return (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)
