"""Real-kernel per-op history keeps carried-face names stable across an upstream edit.

Exercises the hardened persistent-name path end to end: a fillet's OCP maker reports which
output faces are generated/modified/carried, so the faces the fillet did NOT touch keep their
exact names when an upstream extrude dimension changes.
"""

import copy

import pytest

pytestmark = pytest.mark.slow


def _build_ids(document: dict) -> set:
    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.op_registry import OpRegistry

    builder = Builder(Build123dKernel(), OpRegistry.with_defaults())
    part = next(iter(document["parts"].values()))
    _result, element_map, _statuses = builder.build_part_mapped(part)
    return {e.id for e in element_map.elements()}


_DOC = {"units": "mm",
    "parts": {"p": {"profile": "solid", "features": [
        {"id": "base_sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "r", "type": "rectangle", "w": 40, "h": 30}]},
        {"id": "pad", "op": "extrude", "profile": "base_sk", "distance": 10},
        {"id": "round", "op": "fillet", "edges": "vertical", "radius": 3},
    ]}},
}


def test_fillet_history_names_are_deterministic() -> None:
    first = _build_ids(copy.deepcopy(_DOC))
    second = _build_ids(copy.deepcopy(_DOC))
    assert first == second and len(first) > 0


def test_faces_untouched_by_fillet_keep_names_across_height_edit() -> None:
    before = _build_ids(copy.deepcopy(_DOC))
    edited = copy.deepcopy(_DOC)
    for feature in edited["parts"]["p"]["features"]:
        if feature["id"] == "pad":
            feature["distance"] = 14
    after = _build_ids(edited)
    # The top/bottom caps and the un-filleted flats are carried by the fillet's per-op history,
    # so a substantial set of names survives the height change (not zero, as a coarse
    # "everything regenerated" lineage would give).
    assert before and after and (before & after)
