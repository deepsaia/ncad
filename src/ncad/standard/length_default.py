"""Resolve an extruded part's length from the dimensions. Shared by the pipe + i_beam generators.

A length-bearing family (pipe, beam) takes an explicit ``length``; when absent it falls back to the
table's ``length_default`` (a convenient stock cut), and finally to a supplied fallback. Kept as a
typed helper so the checker sees a concrete float (a chained ``dict.get`` default reads as possibly
None). Pure function; no class (a tiny shared helper, not a responsibility).
"""


def resolve_length(dimensions: dict, fallback: float) -> float:
    """The part length: explicit ``length``, else ``length_default``, else ``fallback`` (all mm)."""
    if "length" in dimensions:
        return float(dimensions["length"])
    if "length_default" in dimensions:
        return float(dimensions["length_default"])
    return float(fallback)
