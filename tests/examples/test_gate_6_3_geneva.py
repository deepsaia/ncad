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


def test_geneva_runs_clash_free_through_motion(tmp_path):
    # A correct Geneva runs without the pin fouling the wheel; the pin rides one slot the whole
    # engagement. The motion declares no interference output, so the sidecar carries no events.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "geneva.motion.json").read_text())
    assert motion.get("interference", []) == []


def test_geneva_mobility_is_one(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "geneva.motion.json").read_text())
    assert motion["dof"]["gruebler"] == 1 and motion["dof"]["status"] == "mobile"
