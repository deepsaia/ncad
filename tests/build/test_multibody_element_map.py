from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet
from tests.kernel.fake_kernel import FakeKernel


def test_describe_elements_tags_body_id_for_bodyset():
    k = FakeKernel()
    a = k.extrude(k.polygon_face([(0, 0), (2, 0), (2, 2), (0, 2)], "XY"), distance=2)
    b = k.extrude(k.polygon_face([(5, 0), (7, 0), (7, 2), (5, 2)], "XY"), distance=2)
    bs = BodySet([Body(id="u/body/0", kind="solid", shape=a, created_by="u"),
                  Body(id="u/body/1", kind="solid", shape=b, created_by="u")])
    descriptors = k.describe_elements(bs)
    body_ids = {d["body_id"] for d in descriptors}
    assert body_ids == {"u/body/0", "u/body/1"}


def test_describe_elements_single_shape_has_default_body_id():
    k = FakeKernel()
    box = k.extrude(k.polygon_face([(0, 0), (2, 0), (2, 2), (0, 2)], "XY"), distance=2)
    descriptors = k.describe_elements(box)
    assert descriptors and all(d["body_id"] == "body/0" for d in descriptors)
