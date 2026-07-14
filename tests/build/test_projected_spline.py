"""Projecting a curved (spline) edge into a sketch yields a usable construction spline.

Before 4.4 the kernel refused to project a BSpline/bezier edge (NotImplementedError). Now it
samples the edge at a pinned parameter set and emits an interpolated construction spline, so a
sketch can project a freeform edge just like a straight/arc/circle one.
"""

import pytest

pytestmark = pytest.mark.slow

_DOC = {
    "schema_version": 2, "units": "mm",
    "parts": {"p": {"profile": "solid", "features": [
        {"id": "prof_sk", "op": "sketch", "plane": "XY", "entities": [
            {"id": "p0", "type": "point", "at": [0, 0]},
            {"id": "pm", "type": "point", "at": [10, 6]},
            {"id": "p1", "type": "point", "at": [20, 0]},
            {"id": "p2", "type": "point", "at": [20, -8]},
            {"id": "p3", "type": "point", "at": [0, -8]},
            {"id": "top", "type": "interpolated", "points": ["p0", "pm", "p1"]},
            {"id": "right", "type": "line", "p1": "p1", "p2": "p2"},
            {"id": "bottom", "type": "line", "p1": "p2", "p2": "p3"},
            {"id": "left", "type": "line", "p1": "p3", "p2": "p0"},
        ], "constraints": [
            {"type": "fix", "of": "p0"}, {"type": "fix", "of": "pm"},
            {"type": "fix", "of": "p1"}, {"type": "fix", "of": "p2"},
            {"type": "fix", "of": "p3"}]},
        {"id": "pad", "op": "extrude", "profile": "prof_sk", "distance": 5},
        {"id": "proj_sk", "op": "sketch", "plane": "XY",
         "project": ["select edges where created_by='pad' and type='bspline' and min_z<0.001"],
         "entities": [], "constraints": []},
    ]}},
}


def _build() -> tuple:
    import copy

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    db = DocumentBuilder(Build123dKernel())
    resolved = db._resolve_and_validate(copy.deepcopy(_DOC))
    return db._builder.build_part_mapped(resolved["parts"]["p"])


def test_projected_spline_solves_well_not_refused() -> None:
    result, _element_map, statuses = _build()
    assert result.shape is not None
    proj = next(s for s in statuses if s.feature_id == "proj_sk")
    # The projected spline is accepted and its construction geometry solves (dof 0), rather than
    # raising NotImplementedError as it did before curved-edge projection was supported.
    assert proj.status == "well"


def test_projected_spline_is_deterministic() -> None:
    _r1, e1, _s1 = _build()
    _r2, e2, _s2 = _build()
    ids1 = {e.id for e in e1.elements()}
    ids2 = {e.id for e in e2.elements()}
    assert ids1 == ids2 and len(ids1) > 0
