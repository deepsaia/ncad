import pytest

pytestmark = pytest.mark.slow


def test_text_face_has_glyph_holes_and_extrudes():
    from build123d import extrude

    from ncad.kernel.build123d_kernel import Build123dKernel

    face = Build123dKernel().text_face("Ao", 10.0, "XY")
    # "A" and "o" each have a counter (an inner hole), so at least two inner wires exist.
    faces = face.faces()
    assert sum(len(f.inner_wires()) for f in faces) >= 2
    solid = extrude(face, amount=2)
    assert solid.volume > 0
