import pytest

from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet


def test_body_fields():
    b = Body(id="base/body/0", kind="solid", shape=object(), created_by="base")
    assert b.id == "base/body/0" and b.kind == "solid" and b.created_by == "base"


def test_bodyset_ordered_ids_and_lookup():
    a = Body(id="x/body/0", kind="solid", shape="A", created_by="x")
    b = Body(id="x/body/1", kind="solid", shape="B", created_by="x")
    bs = BodySet([a, b])
    assert bs.ids() == ["x/body/0", "x/body/1"]
    assert bs.by_id("x/body/1").shape == "B"
    assert bs.shapes() == ["A", "B"]
    assert len(bs) == 2


def test_bodyset_unknown_id_raises():
    bs = BodySet([Body(id="x/body/0", kind="solid", shape="A", created_by="x")])
    with pytest.raises(KeyError):
        bs.by_id("nope")
