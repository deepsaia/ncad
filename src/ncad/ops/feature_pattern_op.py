"""The ``feature_pattern`` op: re-apply a tool feature's cut/boss at each pattern location.

The NX/Creo/Fusion "pattern feature": rather than pattern a body, it patterns a feature's
EFFECT. It references a tool-producing feature (whose output solid is the cutter or boss),
transforms N copies of that tool via the body-pattern placement math, and applies ONE
multi-tool boolean (cut or union) to the running solid. Distinct from the 3.x body ``pattern``
(which replicates the running body itself).
"""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.feature_pattern_params import FeaturePatternParamError, feature_pattern_kwargs
from ncad.ops.op_result import OpResult
from ncad.ops.pattern_placements import PatternPlacements


class FeaturePatternOp:
    """Patterns a referenced tool feature's solid and applies one multi-tool boolean."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="feature_pattern has no solid")])
        tool = params.get("__refs__", {}).get("tool")
        if tool is None:
            return OpResult(shape=None, provenance={}, issues=[BuildIssue(
                node_id=feature_id, message="feature_pattern 'tool' feature did not resolve")])
        try:
            kwargs = feature_pattern_kwargs(params)
        except FeaturePatternParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            specs = PatternPlacements(kwargs["pattern"]).specs()
            tools = [tool if not spec else kernel.transform(tool, **spec) for spec in specs]
            if kwargs["operation"] == "cut":
                result = kernel.cut(shape_in, tools)
            else:
                result = kernel.fuse([shape_in, *tools])
        except (KernelOpError, ValueError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
