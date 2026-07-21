"""Generated family documents build to single solids with the expected analytic volume."""

import math

import pytest

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.standard import StandardLibrary

pytestmark = pytest.mark.slow


def _build(doc: dict):
    kernel = Build123dKernel()
    name = next(iter(doc["parts"]))
    result = DocumentBuilder(kernel).build(doc)[name]
    assert result.shape is not None, [i.message for i in result.issues]
    return kernel, result.shape


def test_pipe_volume_matches_annulus():
    kernel, shape = _build(StandardLibrary().generate("pipe", "DN50"))
    # DN50: OD 60.3, wall 3.6, length 300 -> pi*(R^2 - r^2)*L.
    outer_r, inner_r = 60.3 / 2, (60.3 - 2 * 3.6) / 2
    expected = math.pi * (outer_r ** 2 - inner_r ** 2) * 300
    assert kernel.volume(shape) == pytest.approx(expected, rel=1e-3)
    assert kernel.solid_count(shape) == 1


def test_bearing_volume_matches_ring():
    kernel, shape = _build(StandardLibrary().generate("bearing", "6205"))
    # 6205: OD 52, bore 25, width 15.
    expected = math.pi * ((52 / 2) ** 2 - (25 / 2) ** 2) * 15
    assert kernel.volume(shape) == pytest.approx(expected, rel=1e-3)


def test_i_beam_volume_matches_section_area():
    kernel, shape = _build(StandardLibrary().generate("i_beam", "IPE200"))
    # IPE200: h 200, b 100, tw 5.6, tf 8.5, length 2000. Area = 2*b*tf + (h-2tf)*tw.
    area = 2 * 100 * 8.5 + (200 - 2 * 8.5) * 5.6
    assert kernel.volume(shape) == pytest.approx(area * 2000, rel=1e-3)


def test_flange_is_single_solid_with_bolt_holes():
    kernel, shape = _build(StandardLibrary().generate("flange", "NPS4"))
    assert kernel.solid_count(shape) == 1
    # The bored disk minus 8 bolt holes is less than the solid disk of the same envelope.
    disk = math.pi * (228.6 / 2) ** 2 * 23.9
    assert 0 < kernel.volume(shape) < disk
