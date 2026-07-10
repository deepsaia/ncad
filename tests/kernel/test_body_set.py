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


def _three():
    return BodySet([Body(id=f"p/body/{i}", kind="solid", shape=object(), created_by="p")
                    for i in range(3)])


def test_partition_splits_in_and_out_preserving_order():
    ins, out = _three().partition(["p/body/0", "p/body/2"])
    assert [b.id for b in ins] == ["p/body/0", "p/body/2"]
    assert [b.id for b in out] == ["p/body/1"]


def test_partition_in_scope_follows_ids_argument_order():
    ins, _ = _three().partition(["p/body/2", "p/body/0"])
    assert [b.id for b in ins] == ["p/body/2", "p/body/0"]  # target-first for cut


def test_partition_unknown_id_absent_from_in_scope():
    ins, out = _three().partition(["p/body/9"])
    assert ins == []
    assert [b.id for b in out] == ["p/body/0", "p/body/1", "p/body/2"]
