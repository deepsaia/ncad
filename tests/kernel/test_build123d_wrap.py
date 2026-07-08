import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _plate(k):
    return k.extrude(k.polygon_face([(0, 0), (40, 0), (40, 40), (0, 40)], "XY"),
                     distance=10.0)


def _top_face(k, plate):
    faces = [d for d in k.describe_elements(plate) if d["kind"] == "face"]
    return max(faces, key=lambda f: f["mid_z"])["handle"]


def test_engrave_text_reduces_volume():
    k = _kernel()
    plate = _plate(k)
    v0 = k.volume(plate)
    result = k.wrap(plate, _top_face(k, plate), text="AB", font_size=6.0, depth=1.0,
                    mode="engrave")
    assert 0 < k.volume(result) < v0


def test_emboss_text_increases_volume():
    k = _kernel()
    plate = _plate(k)
    v0 = k.volume(plate)
    result = k.wrap(plate, _top_face(k, plate), text="AB", font_size=6.0, depth=1.0,
                    mode="emboss")
    assert k.volume(result) > v0


def test_offset_and_rotation_build():
    k = _kernel()
    plate = _plate(k)
    result = k.wrap(plate, _top_face(k, plate), text="A", font_size=6.0, depth=1.0,
                    mode="emboss", offset=(8.0, -4.0), rotation=45.0)
    assert k.volume(result) > 0
