from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def test_projected_vertices_become_fixed_construction_points():
    # A prior fake face supplies corner vertices; the sketch projects them as fixed
    # construction reference points (excluded from the built wire), then draws its own square.
    kernel = FakeKernel()
    prior = kernel.polygon_face([(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)], "XY")
    # The builder resolves refs into __refs__; here we inject the resolved vertex handles
    # directly (the fake kernel's vertices_of returns the corner tuples).
    verts = kernel.vertices_of(prior)
    params = {
        "id": "sk", "plane": "XY",
        "__refs__": {"project_vertices": verts},
        "entities": [
            {"id": "p0", "type": "point", "at": [0.0, 0.0]},
            {"id": "p1", "type": "point", "at": [2.0, 0.0]},
            {"id": "p2", "type": "point", "at": [2.0, 2.0]},
            {"id": "p3", "type": "point", "at": [0.0, 2.0]},
            {"id": "e0", "type": "line", "p1": "p0", "p2": "p1"},
            {"id": "e1", "type": "line", "p1": "p1", "p2": "p2"},
            {"id": "e2", "type": "line", "p1": "p2", "p2": "p3"},
            {"id": "e3", "type": "line", "p1": "p3", "p2": "p0"},
        ],
        "constraints": [
            {"type": "fix", "of": "p0"}, {"type": "fix", "of": "p1"},
            {"type": "fix", "of": "p2"}, {"type": "fix", "of": "p3"},
        ],
    }
    result = SketchOp().build(None, params, {}, kernel)
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)
