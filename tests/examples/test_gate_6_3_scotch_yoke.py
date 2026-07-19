import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.3"
_MOTION = _GATE / "scotch_yoke.motion.hocon"
_AMP = 30.0


def _assemble(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result["motion"]
    return result


def test_scotch_yoke_clash_free_at_rest(tmp_path):
    _assemble(tmp_path)
    sidecar = json.loads((tmp_path / "scotch_yoke.assembly.json").read_text())
    assert not [f for f in sidecar["interference"] if f["status"] == "interfering"]


def test_yoke_slide_is_a_sine(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "scotch_yoke.motion.json").read_text())
    measure = next(m for m in motion["measures"] if m["unit"] == "mm")
    base = measure["series"][0]
    for frame, value in zip(motion["frames"], measure["series"]):
        want = _AMP * math.sin(math.radians(frame["driver_value"]))
        assert math.isclose(value - base, want, abs_tol=0.5)


def test_scotch_yoke_mobility_is_one(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "scotch_yoke.motion.json").read_text())
    assert motion["dof"]["gruebler"] == 1 and motion["dof"]["status"] == "mobile"


def test_scotch_yoke_deterministic(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    a = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "a"))
    b = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "b"))
    assert (json.loads(Path(a["motion"]).read_text())["measures"]
            == json.loads(Path(b["motion"]).read_text())["measures"])
