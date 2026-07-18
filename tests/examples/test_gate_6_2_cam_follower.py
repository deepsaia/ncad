import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.2"
_MOTION = _GATE / "cam_follower.motion.hocon"
_BASE_R = 20.0     # cam base circle
_LIFT = 12.0       # nose lift above the base circle
_DWELL_DEG = 180.0  # the base-circle dwell spans 0..180 deg


def _assemble(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    return result


def _cam():
    from ncad.assembly.cam_profile import CamProfile

    return CamProfile.from_profile({"base_r": _BASE_R, "segments": [
        {"kind": "dwell", "angle": 180},
        {"kind": "rise", "law": "cycloidal", "angle": 90, "lift": _LIFT},
        {"kind": "return", "law": "cycloidal", "angle": 90},
    ]})


def test_cam_follower_assembles_clash_free_at_rest(tmp_path):
    _assemble(tmp_path)
    sidecar = json.loads((tmp_path / "cam_follower.assembly.json").read_text())
    interfering = [f for f in sidecar["interference"] if f["status"] == "interfering"]
    assert not interfering, f"parts overlap at rest: {interfering}"


def test_follower_lift_measure_tracks_the_cam_profile(tmp_path):
    # The follower's tip starts on the base circle (y = base_r); its world-Y over the revolution is
    # base_r + the cam displacement at that cam angle: flat through the dwell, rising to the nose.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "cam_follower.motion.json").read_text())
    cam = _cam()
    lift = next(m for m in motion["measures"] if m["id"] == "lift")
    assert lift["unit"] == "mm" and len(lift["series"]) == len(motion["frames"])
    for frame, value in zip(motion["frames"], lift["series"]):
        expected = _BASE_R + cam.displacement(frame["driver_value"])
        assert math.isclose(value, expected, abs_tol=0.3)


def test_follower_dwells_then_lifts_to_the_nose(tmp_path):
    # Through the 180 deg dwell the follower is flat on the base circle; the nose reaches base+lift.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "cam_follower.motion.json").read_text())
    lift = next(m for m in motion["measures"] if m["id"] == "lift")
    dwell = [v for f, v in zip(motion["frames"], lift["series"])
             if f["driver_value"] <= _DWELL_DEG - 1e-6]
    assert dwell, "expected frames inside the dwell"
    assert max(dwell) - min(dwell) < 0.3          # flat on the base circle
    assert math.isclose(min(dwell), _BASE_R, abs_tol=0.3)
    assert math.isclose(max(lift["series"]), _BASE_R + _LIFT, abs_tol=0.3)  # the nose


def test_cam_follower_mobility_is_one(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "cam_follower.motion.json").read_text())
    assert motion["dof"]["gruebler"] == 1 and motion["dof"]["status"] == "mobile"


def test_cam_follower_motion_is_deterministic(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    a = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "a"))
    b = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "b"))
    ma = json.loads(Path(a["motion"]).read_text())["measures"]
    mb = json.loads(Path(b["motion"]).read_text())["measures"]
    assert ma == mb
