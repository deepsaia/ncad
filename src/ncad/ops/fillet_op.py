"""The ``fillet`` feature op: round a keyword-selected edge set of the current solid."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.edge_selector import EdgeSelector
from ncad.ops.fillet_params import FilletParamError, fillet_kwargs
from ncad.ops.op_result import OpResult


class FilletOp:
    """Rounds the edges of the incoming solid matching an edge keyword."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message="fillet has no solid")])
        refs = params.get("__refs__", {})
        # A face fillet rounds every edge bounding the referenced faces (distinct from an edge
        # fillet). Face and edge selection are mutually exclusive on one feature.
        faces = refs.get("faces")
        if faces:
            try:
                kwargs = fillet_kwargs(params)
            except FilletParamError as exc:
                return OpResult(shape=None, provenance={},
                                issues=[BuildIssue(node_id=feature_id, message=str(exc))])
            radius = float(kwargs.get("radius") or kwargs["radius_start"])
            try:
                result = kernel.fillet_face(shape_in, faces, radius)
            except KernelOpError as exc:
                return OpResult(shape=None, provenance={},
                                issues=[BuildIssue(node_id=feature_id, message=str(exc))])
            return OpResult(shape=result, provenance={}, issues=[],
                            history=kernel.history([shape_in], result))
        if "edges" in refs:
            edges = refs["edges"] or []
        else:
            keyword = params.get("edges", "all")
            try:
                edges = EdgeSelector().select(kernel.edges_of(shape_in), keyword)
            except ValueError as exc:
                return OpResult(shape=None, provenance={},
                                issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        if not edges:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="fillet: no edges to round")])
        try:
            kwargs = fillet_kwargs(params)
        except FilletParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            if kwargs["variable"]:
                result = kernel.fillet_variable(shape_in, edges, kwargs["radius_start"],
                                                kwargs["radius_end"])
            else:
                result = kernel.fillet_edges(shape_in, edges, kwargs["radius"])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[],
                        history=kernel.history([shape_in], result))
