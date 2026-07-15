"""Gate for the measure kernel surface (bucket 1.8).

Measurement is a KERNEL QUERY, not an authored model feature, so there is no new examples/gate-1.8
.hocon: a contrived part would not exercise anything this real-kernel measurement test does not.
The gate measures a recognizable existing part (the gate-1.7 rocker arm) and asserts the
professional-grade invariants: its oriented bounding box recovers the true part dimensions at an
arbitrary orientation (the CAM stock-size use case), and closest_points / gyradius are
self-consistent.
"""
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_PART = Path(__file__).resolve().parents[2] / "examples" / "gate-1.7" / "rocker_arm.hocon"


def _build():
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    result = DocumentBuilder(kernel).build_file_document(str(_PART))["rocker_arm"]
    return kernel, result.shape


def test_oriented_bbox_is_orientation_invariant():
    from build123d import Axis

    kernel, shape = _build()
    upright = sorted(kernel.oriented_bounding_box(shape)["size"])
    tilted = sorted(kernel.oriented_bounding_box(
        shape.rotate(Axis.Z, 31.0).rotate(Axis.Y, 17.0))["size"])
    # The min bbox reports the same part dimensions no matter how the part is oriented in world
    # space (this is what makes it the CAM stock size).
    assert all(math.isclose(u, t, rel_tol=1e-3) for u, t in zip(upright, tilted))


def test_measure_report_is_self_consistent():
    from build123d import Location, Solid

    kernel, shape = _build()
    # gyradius is a positive triple.
    inertia = kernel.inertia(shape)
    assert len(inertia["gyradius"]) == 3 and all(g > 0 for g in inertia["gyradius"])
    # closest_points to a far probe box equals the scalar distance (consistency invariant).
    probe = Solid.make_box(2, 2, 2).moved(Location((500, 0, 0)))
    pa, pb = kernel.closest_points(shape, probe)
    assert math.isclose(math.dist(pa, pb), kernel.distance(shape, probe), abs_tol=1e-6)
