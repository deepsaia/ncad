"""Tests for the roof builders registry (flat / shed / gable).

Run against the FakeKernel: assert each roof produces positive volume and the right
height envelope, without the OCP backend. Real geometry is covered in the slow build.
"""

import pytest

from ncad.build.roof_builders import ROOF_BUILDERS, build_gable_roof
from tests.kernel.fake_kernel import FakeKernel

_BOUNDS = ((0.0, 0.0), (12.0, 8.0))  # 12 (x) by 8 (y); longer axis is x
_TOP_Z = 3.0


def test_registry_has_flat_shed_gable() -> None:
    assert set(ROOF_BUILDERS) == {"flat", "shed", "gable"}


def test_flat_roof_unchanged_thin_slab() -> None:
    kernel = FakeKernel()
    roof = {"kind": "flat", "thickness": 0.2}

    solid = ROOF_BUILDERS["flat"](kernel, roof, _BOUNDS, _TOP_Z)

    (_, _, minz), (_, _, maxz) = kernel.bounding_box(solid)
    assert minz == pytest.approx(_TOP_Z)
    assert maxz == pytest.approx(_TOP_Z + 0.2)


def test_gable_roof_rises_above_walls() -> None:
    kernel = FakeKernel()
    roof = {"kind": "gable", "pitch": 0.5}  # rise/run

    solid = ROOF_BUILDERS["gable"](kernel, roof, _BOUNDS, _TOP_Z)

    assert kernel.volume(solid) > 0
    (_, _, minz), (_, _, maxz) = kernel.bounding_box(solid)
    assert minz == pytest.approx(_TOP_Z)  # eaves sit on the walls
    # ridge runs along x (longer); span is y=8 → half-span 4 → rise = 0.5*4 = 2
    assert maxz == pytest.approx(_TOP_Z + 2.0, rel=0.05)


def test_shed_roof_high_on_one_side() -> None:
    kernel = FakeKernel()
    roof = {"kind": "shed", "pitch": 0.25}

    solid = ROOF_BUILDERS["shed"](kernel, roof, _BOUNDS, _TOP_Z)

    assert kernel.volume(solid) > 0
    (_, _, minz), (_, _, maxz) = kernel.bounding_box(solid)
    assert minz == pytest.approx(_TOP_Z)
    assert maxz > _TOP_Z  # rises to the high side


def test_gable_default_pitch_when_unspecified() -> None:
    kernel = FakeKernel()

    solid = build_gable_roof(kernel, {"kind": "gable"}, _BOUNDS, _TOP_Z)

    (_, _, _), (_, _, maxz) = kernel.bounding_box(solid)
    assert maxz > _TOP_Z  # some default rise applied
