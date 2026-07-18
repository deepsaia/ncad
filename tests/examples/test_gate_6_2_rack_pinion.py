import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.2"
_MOTION = _GATE / "rack_pinion.motion.hocon"
_MODULE = 3.0
_Z_PINION = 18
_PITCH_R = _MODULE * _Z_PINION / 2.0    # 27 mm: the rack travel per radian


def _assemble(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result["motion"], "the rack and pinion must produce a motion trajectory"
    return result


def test_rack_pinion_assembles_clash_free_at_rest(tmp_path):
    # The rack is phased (half-pitch X offset) so its teeth sit in the pinion's spaces, not jam.
    _assemble(tmp_path)
    sidecar = json.loads((tmp_path / "rack_pinion.assembly.json").read_text())
    interfering = [f for f in sidecar["interference"] if f["status"] == "interfering"]
    assert not interfering, f"rack/pinion teeth overlap at rest: {interfering}"


def test_rack_travel_tracks_pinion_angle_by_pitch_radius(tmp_path):
    # rack travel = pitch_r * pinion_angle (rotation -> translation): 27 mm per radian.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "rack_pinion.motion.json").read_text())
    travel = next(m for m in motion["measures"] if m["id"] == "travel")
    assert travel["unit"] == "mm" and len(travel["series"]) == len(motion["frames"])
    base = travel["series"][0]
    for frame, value in zip(motion["frames"], travel["series"]):
        want = _PITCH_R * math.radians(frame["driver_value"])
        assert math.isclose(value - base, want, abs_tol=0.3)


def test_pinion_pitch_radius_is_the_rack_travel_per_radian(tmp_path):
    from ncad.sketch.gear_profile import GearProfile

    pinion = GearProfile(module=_MODULE, teeth=_Z_PINION)
    assert math.isclose(pinion.rack_travel_per_radian(), _PITCH_R, abs_tol=1e-9)


def test_rack_pinion_mobility_is_one(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "rack_pinion.motion.json").read_text())
    assert motion["dof"]["gruebler"] == 1 and motion["dof"]["status"] == "mobile"


def test_rack_pinion_motion_is_deterministic(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    a = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "a"))
    b = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "b"))
    ma = json.loads(Path(a["motion"]).read_text())["measures"]
    mb = json.loads(Path(b["motion"]).read_text())["measures"]
    assert ma == mb
