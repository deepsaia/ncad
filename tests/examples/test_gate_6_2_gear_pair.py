import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.2"
_MOTION = _GATE / "gear_pair.motion.hocon"
_Z_PINION = 16
_Z_GEAR = 24
_MODULE = 3.0


def _assemble(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result["motion"], "the gear pair must produce a motion trajectory"
    return result


def test_gear_pair_assembles_clash_free_at_rest(tmp_path):
    # The teeth are clocked (gear phase) + backlashed so they interleave with clearance, not jam.
    _assemble(tmp_path)
    sidecar = json.loads((tmp_path / "gear_pair.assembly.json").read_text())
    interfering = [f for f in sidecar["interference"] if f["status"] == "interfering"]
    assert not interfering, f"gear teeth overlap at rest: {interfering}"


def test_gear_turns_at_the_mesh_ratio_reversing_sense(tmp_path):
    # The gear rotation tracks -z_pinion/z_gear of the pinion angle (external mesh reverses sense).
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "gear_pair.motion.json").read_text())
    ratio = _Z_PINION / _Z_GEAR
    for frame in motion["frames"]:
        pinion = math.radians(frame["driver_value"])
        row0 = frame["placements"]["gear"][0]           # gear body-x axis, world
        gear = math.atan2(row0[1], row0[0])             # gear world rotation about Z
        want = -ratio * pinion
        # compare as angles mod 2pi (atan2 wraps); the difference should be ~0.
        diff = (gear - want + math.pi) % (2 * math.pi) - math.pi
        assert abs(diff) < math.radians(0.5)


def test_mesh_center_distance(tmp_path):
    # The two axes sit at the mesh center distance a = (z1+z2)*m/2 = 60 mm.
    from ncad.sketch.gear_profile import GearProfile

    pinion = GearProfile(module=_MODULE, teeth=_Z_PINION)
    gear = GearProfile(module=_MODULE, teeth=_Z_GEAR)
    assert math.isclose(GearProfile.center_distance(pinion, gear),
                        (_Z_PINION + _Z_GEAR) * _MODULE / 2.0, abs_tol=1e-9)


def test_gear_angle_measure_tracks_the_ratio(tmp_path):
    # The `gearAngle` measure reads the gear's turned angle; it should track z_pinion/z_gear of the
    # pinion sweep (unsigned a-vertex-b angle, so it folds at 180 deg). Check the pre-fold samples.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "gear_pair.motion.json").read_text())
    measure = next(m for m in motion["measures"] if m["id"] == "gearAngle")
    assert measure["unit"] == "deg" and len(measure["series"]) == len(motion["frames"])
    ratio = _Z_PINION / _Z_GEAR
    for frame, value in zip(motion["frames"], measure["series"]):
        turned = ratio * frame["driver_value"]          # ideal gear angle, degrees
        if turned <= 180.0 + 1e-9:                       # before the unsigned-angle fold
            assert math.isclose(value, turned, abs_tol=0.5)


def test_gear_pair_mobility_is_one(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "gear_pair.motion.json").read_text())
    assert motion["dof"]["gruebler"] == 1 and motion["dof"]["status"] == "mobile"


def test_gear_pair_motion_is_deterministic(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    a = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "a"))
    b = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "b"))
    fa = json.loads(Path(a["motion"]).read_text())["frames"]
    fb = json.loads(Path(b["motion"]).read_text())["frames"]
    assert fa == fb
