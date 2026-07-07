import math

from tests.kernel.fake_kernel import FakeKernel


def _box(k):
    return k.extrude(k.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"),
                     distance=20.0)


def test_draft_reduces_volume_slightly():
    k = FakeKernel()
    box = _box(k)
    v0 = k.volume(box)
    result = k.draft(box, ["s1", "s2"], angle=5.0, neutral="XY", neutral_offset=0.0)
    expected = v0 * (1.0 - math.sin(math.radians(5.0)) * 0.01 * 2)
    assert k.volume(result) == expected
    assert 0 < k.volume(result) < v0


def test_draft_volume_positive_and_deterministic():
    k = FakeKernel()
    box = _box(k)
    a = k.volume(k.draft(box, ["s1"], angle=10.0, neutral="XY", neutral_offset=0.0))
    b = k.volume(k.draft(box, ["s1"], angle=10.0, neutral="XY", neutral_offset=0.0))
    assert a == b > 0
