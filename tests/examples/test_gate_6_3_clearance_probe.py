import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.3"
_MOTION = _GATE / "clearance_probe.motion.hocon"


def _assemble(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result["motion"]
    return result


def test_clearance_probe_flags_interference_events(tmp_path):
    # This gate is intentionally too tight: the swept arm drives through the fixed post, so
    # MotionInterference must flag the colliding frames with a positive overlap volume.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "clearance_probe.motion.json").read_text())
    events = motion.get("interference", [])
    assert events, "the arm sweeping through the post should flag motion-time interference"
    assert all(e["a"] in ("arm", "base") and e["b"] in ("arm", "base") for e in events)
    assert all(e["volume"] > 0.0 for e in events)


def test_rest_pose_is_clear_clash_is_mid_motion(tmp_path):
    # The post sits at +Y (crank ~90 deg), off the arm's +X rest axis: the REST pose is clash-free
    # and the interference is a MID-MOTION event (the point of motion-time interference).
    result = _assemble(tmp_path)
    rest = json.loads(Path(result["sidecar"]).read_text())
    assert not [f for f in rest["interference"] if f["status"] == "interfering"]
    motion = json.loads((tmp_path / "clearance_probe.motion.json").read_text())
    frames = sorted({e["frame"] for e in motion["interference"]})
    driver = [motion["frames"][f]["driver_value"] for f in frames]
    assert all(45 <= d <= 135 for d in driver), f"clashes not at the post crossing: {driver}"


def test_clearance_probe_mobility_is_one(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "clearance_probe.motion.json").read_text())
    assert motion["dof"]["gruebler"] == 1 and motion["dof"]["status"] == "mobile"
