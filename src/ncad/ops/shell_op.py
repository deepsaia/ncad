"""The ``shell`` feature op: hollow the current solid to a wall thickness."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.shell_params import ShellParamError, shell_kwargs


class ShellOp:
    """Hollows the incoming solid to a wall, optionally removing opening faces."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Shell ``shape_in`` to ``thickness``, removing resolved ``openings`` faces."""
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="shell has no solid")])
        try:
            kwargs = shell_kwargs(params)
        except ShellParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        openings = params.get("__refs__", {}).get("openings")
        try:
            result = kernel.shell(shape_in, kwargs["thickness"], openings=openings or None)
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
