"""The ``thread`` feature op: annotate (cosmetic) or cut (modeled) a thread on the running solid.

Matches the NX/Creo/Fusion Thread feature, which DEFAULTS to a COSMETIC thread: a callout
(e.g. "M10x1.5") recorded as metadata, no geometry change - light, robust, and all a
machinist needs. A real helical thread is an explicit opt-in (``modeled = true``), built by
sweeping a V profile along a helix; it is reliable on a clean cylindrical stud about the
origin axis and best-effort on composed geometry (OCCT thread booleans are fragile, which is
why cosmetic is the default). The size drives pitch + major diameter via the hole-size table
(``size``), or they are given explicitly (``major_d`` + ``pitch``). The axis defaults to Z at
the origin; give ``axis`` (X/Y/Z, {point, dir}, or a datum) to place it.
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
        # Cosmetic thread (the default, like NX/Creo/Fusion): a callout on provenance, no
        # geometry change. The running solid passes through unchanged.
        if not bool(params.get("modeled", False)):
            callout = _callout(params)
            return OpResult(shape=shape_in, provenance={feature_id: f"thread={callout}"},
                            issues=[])
        try:
            major_d, pitch = _thread_dims(params)
            axis_point, axis_dir = _thread_axis(params, refs)
        except (RevolveParamError, ValueError, KeyError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        if "length" not in params:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="modeled thread needs a 'length'")])
        try:
            result = kernel.thread_cut(
                shape_in, axis_point=axis_point, axis_dir=axis_dir, major_d=major_d,
                pitch=pitch, length=float(params["length"]),
                internal=bool(params.get("internal", False)))
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])


def _callout(params: dict) -> str:
    """The cosmetic thread callout string, e.g. 'M10' or 'M10x1.5' or a custom size."""
    if "size" in params:
        size = str(params["size"])
        if "pitch" in params:
            return f"{size}x{float(params['pitch'])}"
        return size
    if "major_d" in params and "pitch" in params:
        return f"M{float(params['major_d'])}x{float(params['pitch'])}"
    return "thread"


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
