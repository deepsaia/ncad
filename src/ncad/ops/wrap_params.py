"""Parse and validate a wrap feature's vocabulary into a wrap description.

A wrap names an ``on`` target face (resolved by the builder) and exactly one profile
source: ``text`` (glyphs at ``font_size``/``font``/``font_style``) or a ``profile`` sketch
ref (resolved by the builder). It extrudes ``depth`` and either ``emboss`` (adds) or
``engrave`` (cuts), placed by ``offset`` (u, v) and ``rotation``. The text-xor-profile
choice is enforced by the op (which knows the resolved profile ref); this helper validates
the text side and the geometry knobs. A contract violation raises WrapParamError.
"""

import logging

logger = logging.getLogger(__name__)

_MODES = ("emboss", "engrave")


class WrapParamError(Exception):
    """A wrap's depth, mode, offset, or font size is missing or invalid."""


def wrap_kwargs(params: dict) -> dict:
    """Return the validated wrap description for a wrap feature.

    ``depth`` (or its alias ``height`` for embossing) is the emboss/engrave amount along the
    face normal. A missing font falls back to the default at the kernel (logged).
    """
    raw_depth = params.get("depth", params.get("height"))
    if raw_depth is None:
        raise WrapParamError("wrap needs a 'depth' (or 'height' for emboss)")
    depth = float(raw_depth)
    if depth <= 0.0:
        raise WrapParamError(f"wrap 'depth'/'height' must be positive; got {raw_depth}")
    font_size = float(params.get("font_size", 5.0))
    if font_size <= 0.0:
        raise WrapParamError(
            f"wrap 'font_size' must be positive; got {params['font_size']}")
    mode = str(params.get("mode", "emboss"))
    if mode not in _MODES:
        raise WrapParamError(f"wrap 'mode' must be one of {_MODES}; got {mode!r}")
    return {
        "text": str(params["text"]) if "text" in params else None,
        "font_size": font_size,
        "font": str(params.get("font", "Arial")),
        "font_style": str(params.get("font_style", "regular")),
        "depth": depth,
        "mode": mode,
        "offset": _offset(params.get("offset", [0.0, 0.0])),
        "rotation": float(params.get("rotation", 0.0)),
    }


def _offset(value: object) -> tuple[float, float]:
    """A [u, v] placement offset in the face plane, else WrapParamError."""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (float(value[0]), float(value[1]))
    raise WrapParamError(f"wrap 'offset' must be a [u, v] pair; got {value!r}")
