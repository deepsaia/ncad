"""Real-kernel reposition_hole: fill a drilled hole and re-cut it at a new location.

Proves the direct "move hole" on a solid: after repositioning, the solid still has exactly one
cylindrical hole, its volume is unchanged (same hole filled and re-cut), and the hole's axis sits
at the target position rather than the original.
"""

import pytest

pytestmark = pytest.mark.slow

_DOC = {"units": "mm",
    "parts": {"p": {"profile": "solid", "features": [
        {"id": "plate_sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "r", "type": "rectangle", "w": 40, "h": 40}]},
        {"id": "plate", "op": "extrude", "profile": "plate_sk", "distance": 10},
        {"id": "drill", "op": "hole", "plane": "XY", "positions": [[-10, -10]], "diameter": 8,
         "through": True},
        {"id": "move", "op": "reposition_hole", "to": [10, 10],
         "hole": "select faces where created_by='drill' and type='cylinder'"},
    ]}},
}


def _build():
    import copy

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    db = DocumentBuilder(kernel)
    resolved = db._resolve_and_validate(copy.deepcopy(_DOC))
    result, _emap, _statuses = db._builder.build_part_mapped(resolved["parts"]["p"])
    return kernel, result


def test_reposition_hole_moves_the_hole_and_preserves_volume():
    kernel, result = _build()
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]
    # A 40x40x10 plate minus one dia-8 through hole.
    from math import pi
    expected = 40 * 40 * 10 - pi * 16 * 10
    assert abs(kernel.volume(result.shape) - expected) < 1.0


def test_reposition_hole_cylinder_axis_sits_at_the_target():
    kernel, result = _build()
    cylinders = [kernel.axis_of(f) for f in result.shape.faces()]
    cylinders = [c for c in cylinders if c is not None]
    assert len(cylinders) == 1
    loc = cylinders[0]["location"]
    # The hole moved from (-10, -10) to (10, 10) in the drilling plane.
    assert abs(loc[0] - 10.0) < 1e-6 and abs(loc[1] - 10.0) < 1e-6
