"""The ``boolean`` feature op: combine solids (ref mode) or a part's own bodies (scope mode)."""

from typing import Any

from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet
from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.boolean_params import BooleanParamError, boolean_kwargs
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.refs.selector import Selector
from ncad.refs.selector_error import SelectorError


class BooleanOp:
    """Combines prior-feature refs (ref mode) or named running bodies (scope mode)."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        try:
            kwargs = boolean_kwargs(params)
        except BooleanParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            # Two modes: ref mode combines resolved target/tool(s); scope mode combines named
            # bodies of the running multibody shape. boolean_kwargs picks the mode.
            if kwargs["mode"] == "scope":
                result = self._scope_mode(shape_in, kwargs, feature_id, kernel)
            else:
                result = self._ref_mode(params, kwargs, feature_id, kernel)
        except (KernelOpError, ValueError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        if isinstance(result, BuildIssue):
            return OpResult(shape=None, provenance={}, issues=[result])
        # Booleans keep geometric carry-forward (history None): build123d's post-boolean
        # coplanar-face merge invalidates the OCP maker's per-face lineage, so real per-op
        # boolean names need a composed BRepTools_History (a documented follow-up).
        return OpResult(shape=result, provenance={}, issues=[])

    def _ref_mode(self, params: dict, kwargs: dict, feature_id: str, kernel: Kernel) -> Any:
        """Combine a target ref with one or more tool refs."""
        refs = params.get("__refs__", {})
        target = refs.get("target")
        tools = refs["tools"] if "tools" in refs else (
            [refs.get("tool")] if refs.get("tool") is not None else [])
        if target is None or not tools or any(t is None for t in tools):
            return BuildIssue(node_id=feature_id,
                              message="boolean needs a resolved target and tool(s)")
        operation = kwargs["operation"]
        # union + merge=false keeps the operands as separate bodies (3.0 keep-separate);
        # union_bodies flattens a BodySet operand. Pass each operand's SOURCE feature id so a
        # kept-separate body keeps its provenance (and material) instead of taking the union's
        # id: the target's source is params["target"], the tools' is params["tool"]/["tools"].
        if operation == "union" and not kwargs["merge"]:
            tool_names = params["tools"] if "tools" in params else [params.get("tool")]
            sources = [params.get("target"), *tool_names]
            return kernel.union_bodies([target, *tools], origin=feature_id, sources=sources)
        # A ref (target or tool) may itself be a BodySet (e.g. a pattern's output used as the
        # cut tools). The kernel booleans take flat shape lists, so expand BodySets into their
        # member shapes first. A cut removes every flattened tool from the (flattened) target.
        target_shapes = _flatten(target)
        tool_shapes = [s for t in tools for s in _flatten(t)]
        if operation == "cut":
            return kernel.cut(_single(target_shapes), tool_shapes)
        if operation == "union":
            return kernel.fuse([*target_shapes, *tool_shapes])
        return kernel.intersect([*target_shapes, *tool_shapes])

    def _scope_mode(self, shape_in: Any, kwargs: dict, feature_id: str,
                    kernel: Kernel) -> Any:
        """Combine named bodies of the running BodySet; pass the rest through untouched.

        ``scope`` is an explicit body-id list, or is resolved here from a ``scope_query``
        (``select bodies where ...``) against the running BodySet.
        """
        scope = kwargs["scope"]
        if kwargs.get("scope_query") is not None:
            if not isinstance(shape_in, BodySet):
                return BuildIssue(node_id=feature_id, message=(
                    "boolean scope query needs a multibody running shape"))
            resolved = _select_body_ids(kwargs["scope_query"], shape_in)
            if isinstance(resolved, BuildIssue):
                return resolved
            if not resolved:
                query = kwargs["scope_query"]
                return BuildIssue(node_id=feature_id,
                                  message=f"scope query matched no bodies: {query!r}")
            scope = resolved
        if not isinstance(shape_in, BodySet):
            # A single-body running shape: scope only makes sense for its one body. More than
            # one requested id cannot resolve, so that is an error.
            if len(scope) > 1:
                return BuildIssue(node_id=feature_id,
                                  message="boolean scope names multiple bodies but the running "
                                          "shape is a single body")
            return shape_in  # one id on a single body: no-op
        in_scope, out_scope = shape_in.partition(scope)
        if len(in_scope) != len(scope):
            return BuildIssue(node_id=feature_id,
                              message=f"boolean scope references unknown body id(s): {scope}")
        combined = self._combine(kwargs["operation"], [b.shape for b in in_scope], kernel)
        # Build the result BodySet MANUALLY so passed-through bodies KEEP their ids and only
        # the new combined geometry is born as feature_id/body/0. union_bodies would re-mint
        # every id, destroying the passed-through identities.
        result_bodies = [Body(id=f"{feature_id}/body/0", kind="solid", shape=combined,
                              created_by=feature_id), *out_scope]
        if len(result_bodies) == 1:
            return combined       # only one body remains: back to a single shape
        return BodySet(result_bodies)

    @staticmethod
    def _combine(operation: str, shapes: list, kernel: Kernel) -> Any:
        """Combine ``shapes`` (ordered) per operation into one shape."""
        if operation == "cut":
            return kernel.cut(shapes[0], shapes[1:])
        if operation == "union":
            return kernel.fuse(shapes)
        return kernel.intersect(shapes)


def _flatten(shape: Any) -> list:
    """Expand a BodySet into its member shapes; a plain shape becomes a one-element list.

    The kernel booleans (cut/fuse/intersect) take flat shape lists, but a boolean operand can
    be a multibody BodySet (e.g. a pattern's output used as cut tools), so callers flatten first.
    """
    if isinstance(shape, BodySet):
        return list(shape.shapes())
    return [shape]


def _single(shapes: list) -> Any:
    """The single cut target. A cut target must be one solid.

    A cut removes tools from ONE target; a multibody cut target is ambiguous (which body?),
    so raise rather than guess. Use scope mode or a per-body op for multibody targets.
    """
    if len(shapes) != 1:
        raise ValueError(
            "boolean cut target must be a single body; got a multibody target "
            "(cut per body or use scope mode)")
    return shapes[0]


class _BodyElement:
    """Adapts a Body to the Selector element interface (kind + attrs).

    A body's queryable attributes are its born-once id (as ``tag``) and its creating feature
    (``created_by``). Material-in-scope needs the builder's feature->material map, which the op
    does not have, so ``material`` selection over bodies is a follow-up (use ``tag`` /
    ``created_by`` here).
    """

    def __init__(self, body: Any) -> None:
        self._body = body
        self.kind = "body"
        self.attrs = {"tag": body.id, "created_by": body.created_by}


def _select_body_ids(query: str, bodies: BodySet) -> Any:
    """Resolve a ``select bodies where ...`` query to the matching body ids, or a BuildIssue."""
    elements = [_BodyElement(b) for b in bodies.bodies]
    try:
        matched = Selector().select(query, elements)
    except SelectorError as exc:
        return BuildIssue(node_id="boolean", message=f"scope query: {exc}")
    return [e.attrs["tag"] for e in matched]
