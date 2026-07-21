"""DfmFacts reads thickness, envelope, and hole diameters from a real B-rep part."""

import pytest

from ncad.build.dfm_facts import DfmFacts
from ncad.kernel.build123d_kernel import Build123dKernel

pytestmark = pytest.mark.slow


def test_extract_plate_with_hole():
    kernel = Build123dKernel()
    plate = kernel.extrude(
        kernel.polygon_face([(0, 0), (60, 0), (60, 40), (0, 40)], "XY"), 3.0)
    hole = kernel.cylinder((20, 20, -1), "Z", diameter=5.0, length=6.0)
    part = kernel.cut(plate, [hole])

    facts = DfmFacts(kernel).extract(part)

    assert facts["min_wall_thickness"] == pytest.approx(3.0)
    assert facts["bbox_size"] == pytest.approx([60.0, 40.0, 3.0])
    assert facts["smallest_hole_diameter"] == pytest.approx(5.0)
    assert len(facts["holes"]) == 1


def test_solid_without_holes_has_none_hole_diameter():
    kernel = Build123dKernel()
    block = kernel.extrude(
        kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), 5.0)

    facts = DfmFacts(kernel).extract(block)

    assert facts["smallest_hole_diameter"] is None
    assert facts["holes"] == []
