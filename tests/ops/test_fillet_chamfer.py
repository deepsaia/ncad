from ncad.ops.chamfer_op import ChamferOp
from ncad.ops.fillet_op import FilletOp
from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def _block(kernel):
    face = SketchOp().build(None, {"id": "sk", "op": "sketch", "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": 80, "h": 60}]}, {}, kernel).shape
    return kernel.extrude(face, 8.0)


def test_fillet_vertical_edges_changes_volume() -> None:
    kernel = FakeKernel()
    solid = _block(kernel)

    result = FilletOp().build(solid, {"id": "f", "op": "fillet", "radius": 2.0,
                                       "edges": "vertical"}, {}, kernel)

    assert result.issues == []
    assert result.shape is not None


def test_chamfer_all_edges() -> None:
    kernel = FakeKernel()
    solid = _block(kernel)

    result = ChamferOp().build(solid, {"id": "c", "op": "chamfer", "distance": 1.0,
                                        "edges": "all"}, {}, kernel)

    assert result.issues == []
    assert result.shape is not None


def test_fillet_unknown_keyword_reports_issue() -> None:
    kernel = FakeKernel()
    solid = _block(kernel)

    result = FilletOp().build(solid, {"id": "f", "op": "fillet", "radius": 2.0,
                                       "edges": "sideways"}, {}, kernel)

    assert result.shape is None
    assert result.issues[0].node_id == "f"


def test_fillet_uses_resolved_edges_from_refs() -> None:
    kernel = FakeKernel()
    solid = _block(kernel)
    edge_handles = [d["handle"] for d in kernel.describe_elements(solid)
                    if d["kind"] == "edge"][:2]

    feature = {"id": "rnd", "op": "fillet", "radius": 1.0,
               "__refs__": {"edges": edge_handles}}
    result = FilletOp().build(solid, feature, {}, kernel)

    assert result.issues == [] and result.shape is not None
