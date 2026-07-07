"""The ``sweep`` feature op: sweep a profile along a path wire or a generated helix."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.sweep_params import SweepParamError, sweep_kwargs


class SweepOp:
    """Sweeps an upstream profile face along a path wire or a generated helix."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Sweep the profile along its ``path`` (an open wire) or generated ``helix``."""
        feature_id = params["id"]
        refs = params.get("__refs__", {})
        profile = refs.get("profile") or shape_in
        if profile is None:
            return OpResult(shape=None, provenance={}, issues=[BuildIssue(
                node_id=feature_id, message="sweep has no profile face")])
        try:
            kwargs = sweep_kwargs(params, refs)
        except SweepParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        path, path_error = self._path_of(kwargs, params, refs, kernel)
        if path_error is not None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=path_error)])
        try:
            solid = kernel.sweep(profile, path, sections=refs.get("sections"),
                                 guides=refs.get("guides"),
                                 is_frenet=kwargs["is_frenet"],
                                 transition=kwargs["transition"])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=solid, provenance={}, issues=[])

    def _path_of(self, kwargs: dict, params: dict, refs: dict,
                 kernel: Kernel) -> tuple[Any, str | None]:
        """The sweep path: a generated helix, or the resolved ``path`` wire ref."""
        if "helix" in kwargs:
            h = kwargs["helix"]
            return kernel.helix_path(h["pitch"], h["height"], h["radius"],
                                     axis_point=h["axis_point"], axis_dir=h["axis_dir"],
                                     lefthand=h["lefthand"],
                                     cone_angle=h["cone_angle"]), None
        path = refs.get("path")
        if path is None:
            return None, f"sweep path {params.get('path')!r} did not resolve to a wire"
        return path, None
