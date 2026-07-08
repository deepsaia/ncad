"""The ``wrap`` feature op: emboss or engrave a profile onto a flat face of the solid."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.wrap_params import WrapParamError, wrap_kwargs


class WrapOp:
    """Emboss/engrave text or a referenced profile onto a target face of the solid."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Wrap a ``text`` or ``profile`` onto the ``on`` face of ``shape_in``."""
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="wrap has no solid")])
        refs = params.get("__refs__", {})
        on_element = refs.get("on")
        if on_element is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="wrap has no target face (on)")])
        profile = refs.get("profile")
        has_text = "text" in params
        # Exactly one profile source: both present (True == True) or neither (False ==
        # False) is an error; exactly one passes the XOR guard.
        if has_text == (profile is not None):
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="wrap needs exactly one of 'text' "
                                                       "or 'profile'")])
        try:
            kwargs = wrap_kwargs(params)
        except WrapParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            result = kernel.wrap(shape_in, on_element.handle, text=kwargs["text"],
                                 profile=profile, font_size=kwargs["font_size"],
                                 font=kwargs["font"], font_style=kwargs["font_style"],
                                 depth=kwargs["depth"], mode=kwargs["mode"],
                                 offset=kwargs["offset"], rotation=kwargs["rotation"])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
