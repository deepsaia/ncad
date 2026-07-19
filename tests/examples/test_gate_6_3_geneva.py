import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.3"
_MOTION = _GATE / "geneva.motion.hocon"


def _assemble(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result["motion"]
    return result


def test_geneva_clash_free_at_rest(tmp_path):
    _assemble(tmp_path)
    sidecar = json.loads((tmp_path / "geneva.assembly.json").read_text())
    assert not [f for f in sidecar["interference"] if f["status"] == "interfering"]


def test_wheel_dwells_then_indexes_ninety_degrees(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "geneva.motion.json").read_text())
    wa = next(m for m in motion["measures"] if m["id"] == "wheelAngle")
    series = wa["series"]
    # The wheel indexes ~90 deg over the revolution, dwelling before/after the engagement window.
    span = max(series) - min(series)
    assert 80.0 <= span <= 100.0
    # The first quarter of frames dwell (little change) before the engagement centred at 180 deg.
    quarter = len(series) // 4
    assert abs(series[quarter] - series[0]) < 15.0


def test_geneva_reports_interference_events(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "geneva.motion.json").read_text())
    events = motion.get("interference", [])
    assert events, "the pin/slot engagement should flag motion-time interference"
    assert all("frame" in e and "volume" in e for e in events)
    # The pinch is around the engagement centre (crank 180 deg, ~frame 36 of 72).
    frames = {e["frame"] for e in events}
    assert any(24 <= f <= 48 for f in frames)


def test_geneva_mobility_is_one(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "geneva.motion.json").read_text())
    assert motion["dof"]["gruebler"] == 1 and motion["dof"]["status"] == "mobile"
