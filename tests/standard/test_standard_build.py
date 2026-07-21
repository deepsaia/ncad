"""Generated standard-part documents build to solids with the expected analytic volume."""

import math

import pytest

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.standard import StandardLibrary

pytestmark = pytest.mark.slow


def _build_volume(doc: dict) -> float:
    kernel = Build123dKernel()
    name = next(iter(doc["parts"]))
    result = DocumentBuilder(kernel).build(doc)[name]
    assert result.shape is not None, [i.message for i in result.issues]
    return kernel.volume(result.shape)


def test_washer_m8_volume_matches_annulus():
    # ISO 7089 M8: id 8.4, od 16, thickness 1.6 -> pi*(R^2 - r^2)*t.
    doc = StandardLibrary().generate("washer", "M8")
    expected = math.pi * ((16.0 / 2) ** 2 - (8.4 / 2) ** 2) * 1.6
    assert _build_volume(doc) == pytest.approx(expected, rel=1e-3)


def test_hex_nut_m8_volume_matches_prism_minus_bore():
    # Regular hexagon area = (3*sqrt(3)/2)*R^2; volume = (area - pi*(d/2)^2)*thickness.
    doc = StandardLibrary().generate("hex_nut", "M8")
    circumradius = (13.0 / 2.0) / math.cos(math.pi / 6.0)
    hex_area = (3.0 * math.sqrt(3.0) / 2.0) * circumradius ** 2
    expected = (hex_area - math.pi * (8.0 / 2.0) ** 2) * 6.8
    assert _build_volume(doc) == pytest.approx(expected, rel=1e-3)


def test_custom_washer_builds():
    doc = StandardLibrary().generate_custom(
        "washer", {"inner_diameter": 5.0, "outer_diameter": 14.0, "thickness": 1.2})
    expected = math.pi * ((14.0 / 2) ** 2 - (5.0 / 2) ** 2) * 1.2
    assert _build_volume(doc) == pytest.approx(expected, rel=1e-3)
