"""The ``chamfer`` feature op: bevel a keyword-selected edge set of the current solid."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.chamfer_params import ChamferParamError, chamfer_kwargs
from ncad.ops.edge_selector import EdgeSelector
from ncad.ops.op_result import OpResult


class ChamferOp:
    """Bevels the edges of the incoming solid matching an edge keyword."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message="chamfer has no solid")])
        refs = params.get("__refs__", {})
        # A vertex chamfer facets the corner vertices of the referenced geometry (bevels the
        # edges meeting each). Distinct from an edge chamfer.
        vertices = refs.get("vertices")
        if vertices:
            try:
                kwargs = chamfer_kwargs(params)
            except ChamferParamError as exc:
                return OpResult(shape=None, provenance={},
                                issues=[BuildIssue(node_id=feature_id, message=str(exc))])
            try:
                result = kernel.chamfer_vertices(shape_in, vertices, kwargs["distance"])
            except KernelOpError as exc:
                return OpResult(shape=None, provenance={},
                                issues=[BuildIssue(node_id=feature_id, message=str(exc))])
            return OpResult(shape=result, provenance={}, issues=[])
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
                                               message="chamfer: no edges to bevel")])
        try:
            kwargs = chamfer_kwargs(params)
        except ChamferParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            result = kernel.chamfer_edges(shape_in, edges, kwargs["distance"],
                                          distance2=kwargs["distance2"],
                                          angle=kwargs["angle"])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
