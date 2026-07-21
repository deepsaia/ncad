"""Generated pipe-fitting documents build to hollow single solids."""

import pytest

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.standard import StandardLibrary

pytestmark = pytest.mark.slow


def _build(subtype: str, designation: str):
    kernel = Build123dKernel()
    doc = StandardLibrary().generate("pipe_fitting", designation, subtype=subtype)
    name = next(iter(doc["parts"]))
    result = DocumentBuilder(kernel).build(doc)[name]
    assert result.shape is not None, [i.message for i in result.issues]
    return kernel, result.shape


def test_elbow_builds_single_hollow_solid():
    kernel, shape = _build("elbow", "DN50")
    assert kernel.solid_count(shape) == 1
    assert kernel.volume(shape) > 0.0
    # A 90-degree bend: the part spans both the start (+Z) and end (+X) directions.
    (x0, _, z0), (x1, _, z1) = kernel.bounding_box(shape)
    assert (x1 - x0) > 30.0 and (z1 - z0) > 30.0


def test_tee_builds_single_solid_spanning_run_and_branch():
    kernel, shape = _build("tee", "DN50")
    assert kernel.solid_count(shape) == 1
    (x0, _, z0), (x1, _, z1) = kernel.bounding_box(shape)
    # run along X (full run_length) is wider than the branch rise along Z.
    assert (x1 - x0) > (z1 - z0)


def test_reducer_builds_single_solid():
    kernel, shape = _build("reducer", "DN80xDN50")
    assert kernel.solid_count(shape) == 1
    assert kernel.volume(shape) > 0.0
