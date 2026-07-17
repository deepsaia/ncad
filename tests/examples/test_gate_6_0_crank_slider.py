import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.0"
_ASM = _GATE / "crank_slider.asm.hocon"
_MOTION = _GATE / "crank_slider.motion.hocon"
_R = 20.0   # crank radius (matches crank_slider.hocon: crank-pin bore at x = 20)
_L = 70.0   # rod length: sqrt(20^2 + 67^2) = 70, so the wrist rests at y = sqrt(L^2 - R^2) = 67
# The piston's wrist bore, in the piston's local frame (metres). The part is authored in the
# assembled position, so its local frame == world at rest; the wrist sits at (0, 67, 0) mm.
_WRIST_LOCAL = (0.0, 0.067, 0.0)


def _apply(p, m):
    return tuple(sum(p[k] * m[k][i] for k in range(3)) + m[3][i] for i in range(3))


def _wrist_y(placement):
    # The piston's wrist point in world metres -> mm; its y is the slider stroke.
    return _apply(_WRIST_LOCAL, placement)[1] * 1000.0


def _assemble(tmp_path):
    # Build via the MOTION document (a first-class kind): it drives the referenced assembly and
    # writes both the scene sidecar and the trajectory.
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    return result


def test_crank_slider_assembles_clash_free_at_rest(tmp_path):
    # A green gate must mean a correctly ASSEMBLED mechanism, not just correct motion math: no two
    # parts may interfere (overlap in volume) at the rest pose. Touching (at the joints) is fine.
    _assemble(tmp_path)
    sidecar = json.loads((tmp_path / "crank_slider.assembly.json").read_text())
    interfering = [f for f in sidecar["interference"] if f["status"] == "interfering"]
    assert not interfering, f"parts overlap at rest: {interfering}"


def test_crank_slider_motion_matches_analytic_stroke(tmp_path):
    result = _assemble(tmp_path)
    assert result.get("motion") is not None
    motion = json.loads((tmp_path / "crank_slider.motion.json").read_text())
    assert len(motion["frames"]) == 73  # steps = 72 -> 73 inclusive frames

    # Declared joints + one driver reproduce the closed-form piston stroke
    # yP = R sin(theta) + sqrt(L^2 - (R cos theta)^2), with NO per-mechanism formula.
    for frame in motion["frames"]:
        theta = math.radians(frame["driver_value"])
        analytic = _R * math.sin(theta) + math.sqrt(_L ** 2 - (_R * math.cos(theta)) ** 2)
        assert math.isclose(_wrist_y(frame["placements"]["piston"]), analytic, abs_tol=1.0)


def test_crank_slider_piston_reciprocates(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "crank_slider.motion.json").read_text())
    ys = [_wrist_y(f["placements"]["piston"]) for f in motion["frames"]]
    # Top dead centre ~ R + L = 90, bottom ~ L - R = 50: a 40 mm stroke, peaking mid-sweep (not at
    # an endpoint), i.e. the piston rises then falls (reciprocation), not a monotonic drift.
    assert math.isclose(max(ys) - min(ys), 2.0 * _R, abs_tol=1.5)
    assert ys.index(max(ys)) not in (0, len(ys) - 1)
