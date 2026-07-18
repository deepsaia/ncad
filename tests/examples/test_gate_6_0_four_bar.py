import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.0"
_MOTION = _GATE / "four_bar.motion.hocon"
# Ground pivots + link lengths (match four_bar.hocon): A=(0,0), D=(90,0); crank 30, coupler 80,
# rocker 60. Grashof crank-rocker, so the crank turns fully and the rocker sweeps a bounded arc.
_D = (0.090, 0.0, 0.0)                 # ground pivot D, metres
_C_LOCAL = (0.083333, 0.059628, 0.0)   # coupler-rocker pin C in each moving part's local frame


def _apply(p, m):
    return tuple(sum(p[k] * m[k][i] for k in range(3)) + m[3][i] for i in range(3))


def _assemble(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    return result


def test_four_bar_assembles_clash_free_at_rest(tmp_path):
    # A green gate must mean a correctly ASSEMBLED mechanism: no two parts overlap in volume at
    # rest (touching at the pins is fine).
    _assemble(tmp_path)
    sidecar = json.loads((tmp_path / "four_bar.assembly.json").read_text())
    interfering = [f for f in sidecar["interference"] if f["status"] == "interfering"]
    assert not interfering, f"parts overlap at rest: {interfering}"


def test_four_bar_closed_loop_stays_closed(tmp_path):
    # The first CLOSED-LOOP gate: at every frame the coupler's C pin and the rocker's C pin must
    # coincide (the loop is closed), which only holds if the solver converged the loop each step.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "four_bar.motion.json").read_text())
    assert len(motion["frames"]) == 73  # steps = 72 -> 73 inclusive frames
    for frame in motion["frames"]:
        assert frame["status"] == "solved"
        c_coupler = _apply(_C_LOCAL, frame["placements"]["coupler"])
        c_rocker = _apply(_C_LOCAL, frame["placements"]["rocker"])
        gap_mm = math.dist(c_coupler, c_rocker) * 1000.0
        assert gap_mm < 0.5, f"loop open by {gap_mm:.3f} mm at {frame['driver_value']} deg"


def test_four_bar_rocker_sweeps_bounded_arc(tmp_path):
    # As the crank turns a full revolution the output rocker oscillates over a bounded, non-trivial
    # arc (a crank-rocker), not a full turn: the D->C angle spans well under 360 deg.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "four_bar.motion.json").read_text())
    angles = []
    for frame in motion["frames"]:
        c = _apply(_C_LOCAL, frame["placements"]["rocker"])
        angles.append(math.degrees(math.atan2(c[1] - _D[1], c[0] - _D[0])))
    sweep = max(angles) - min(angles)
    assert 20.0 < sweep < 180.0, f"rocker sweep {sweep:.1f} deg is not a bounded crank-rocker arc"


def test_four_bar_solve_is_deterministic(tmp_path):
    # Same document + driver -> identical trajectory across two builds (determinism the design
    # depends on: same spec >> identical geometry/motion).
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    a = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "a"))
    b = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "b"))
    fa = json.loads(Path(a["motion"]).read_text())["frames"]
    fb = json.loads(Path(b["motion"]).read_text())["frames"]
    assert [f["placements"]["rocker"] for f in fa] == [f["placements"]["rocker"] for f in fb]
