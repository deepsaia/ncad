from tests.kernel.fake_kernel import FakeKernel


def _plate(k):
    return k.extrude(k.polygon_face([(0, 0), (40, 0), (40, 40), (0, 40)], "XY"),
                     distance=10.0)


def test_emboss_adds_volume():
    k = FakeKernel()
    plate = _plate(k)
    v0 = k.volume(plate)
    result = k.wrap(plate, object(), text="AB", font_size=8.0, depth=2.0, mode="emboss")
    assert k.volume(result) > v0


def test_engrave_removes_volume():
    k = FakeKernel()
    plate = _plate(k)
    v0 = k.volume(plate)
    result = k.wrap(plate, object(), text="AB", font_size=8.0, depth=2.0, mode="engrave")
    assert 0 < k.volume(result) < v0


def test_emboss_and_engrave_symmetric_delta():
    k = FakeKernel()
    plate = _plate(k)
    v0 = k.volume(plate)
    emb = k.volume(k.wrap(plate, object(), text="AB", font_size=8.0, depth=2.0,
                          mode="emboss"))
    eng = k.volume(k.wrap(plate, object(), text="AB", font_size=8.0, depth=2.0,
                          mode="engrave"))
    assert (emb - v0) == (v0 - eng)


def test_wrap_deterministic():
    k = FakeKernel()
    plate = _plate(k)
    a = k.volume(k.wrap(plate, object(), text="AB", font_size=8.0, depth=2.0))
    b = k.volume(k.wrap(plate, object(), text="AB", font_size=8.0, depth=2.0))
    assert a == b
