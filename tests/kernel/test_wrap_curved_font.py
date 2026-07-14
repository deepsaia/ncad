import pytest

pytestmark = pytest.mark.slow


def test_emboss_on_cylinder_adds_material():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    cyl = Solid.make_cylinder(10, 30)
    face = next(f for f in cyl.faces() if f.geom_type.name.lower() == "cylinder")
    embossed = kernel.wrap(cyl, face, text="AB", font_size=4.0, depth=1.0, mode="emboss")
    # Embossed text on the curved wall adds raised material.
    assert embossed.volume > cyl.volume


def test_engrave_on_cylinder_removes_material():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    cyl = Solid.make_cylinder(10, 30)
    face = next(f for f in cyl.faces() if f.geom_type.name.lower() == "cylinder")
    engraved = kernel.wrap(cyl, face, text="AB", font_size=4.0, depth=1.0, mode="engrave")
    assert engraved.volume < cyl.volume


def test_missing_font_falls_back_and_logs(caplog):
    import logging

    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = Solid.make_box(30, 20, 4)
    top = next(f for f in box.faces() if f.normal_at().Z > 0.9)
    with caplog.at_level(logging.WARNING):
        result = kernel.wrap(box, top, text="Hi", font_size=5.0, depth=1.0, mode="emboss",
                             font="NoSuchFont12345")
    assert result.volume > box.volume
    assert any("font" in r.message.lower() for r in caplog.records)
