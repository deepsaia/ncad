import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_GATE = Path(__file__).resolve().parents[2] / "examples" / "gate-6.1"
_MOTION = _GATE / "reciprocating_pump.motion.hocon"
_R = 20.0        # crank radius (crank-pin bore at x = 20)
_L = 70.0        # rod length: sqrt(20^2 + 67^2) = 70, wrist rests at y = sqrt(L^2 - R^2) = 67
_BORE_D = 28.0   # plunger bore diameter (matches the swept_volume measure)
_CROWN_LOCAL = (0.0, 0.067, 0.0)   # plunger crown in the plunger's local frame (metres)


def _apply(p, m):
    return tuple(sum(p[k] * m[k][i] for k in range(3)) + m[3][i] for i in range(3))


def _assemble(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path))
    assert not result["issues"], result["issues"]
    return result


def test_pump_assembles_clash_free_at_rest(tmp_path):
    _assemble(tmp_path)
    sidecar = json.loads((tmp_path / "reciprocating_pump.assembly.json").read_text())
    interfering = [f for f in sidecar["interference"] if f["status"] == "interfering"]
    assert not interfering, f"parts overlap at rest: {interfering}"


def test_pump_stroke_measure_matches_analytic(tmp_path):
    # The stroke measure (plunger crown world-Y over time) reproduces the closed-form crank-slider
    # stroke yP = R sin(theta) + sqrt(L^2 - (R cos theta)^2), from the declared joints + one driver.
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "reciprocating_pump.motion.json").read_text())
    assert len(motion["frames"]) == 73
    stroke = next(m for m in motion["measures"] if m["id"] == "stroke")
    assert stroke["unit"] == "mm" and len(stroke["series"]) == 73
    for frame, value in zip(motion["frames"], stroke["series"]):
        theta = math.radians(frame["driver_value"])
        analytic = _R * math.sin(theta) + math.sqrt(_L ** 2 - (_R * math.cos(theta)) ** 2)
        assert math.isclose(value, analytic, abs_tol=1.0)


def test_pump_swept_volume_matches_displacement(tmp_path):
    # displacement = full stroke (2R) x bore area, in mL (mm^3 / 1000).
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "reciprocating_pump.motion.json").read_text())
    disp = next(m for m in motion["measures"] if m["id"] == "displacement")
    expected_ml = (2.0 * _R) * math.pi / 4.0 * _BORE_D ** 2 / 1000.0
    assert disp["unit"] == "mL"
    assert math.isclose(disp["value"], expected_ml, abs_tol=0.5)


def test_pump_crown_trace_has_a_point_per_frame(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "reciprocating_pump.motion.json").read_text())
    trace = next(t for t in motion["traces"] if t["id"] == "crownPath")
    assert len(trace["polyline"]) == len(motion["frames"])
    # The crown trace is a straight reciprocating line (plunger slides on +Y): x, z ~ constant.
    xs = [p[0] for p in trace["polyline"]]
    zs = [p[2] for p in trace["polyline"]]
    assert max(xs) - min(xs) < 1e-3 and max(zs) - min(zs) < 1e-3


def test_pump_mobility_is_one(tmp_path):
    _assemble(tmp_path)
    motion = json.loads((tmp_path / "reciprocating_pump.motion.json").read_text())
    assert motion["dof"]["gruebler"] == 1 and motion["dof"]["status"] == "mobile"


def test_pump_motion_is_deterministic(tmp_path):
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    a = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "a"))
    b = MotionBuilder(Build123dKernel()).build(str(_MOTION), str(tmp_path / "b"))
    ma = json.loads(Path(a["motion"]).read_text())["measures"]
    mb = json.loads(Path(b["motion"]).read_text())["measures"]
    assert ma == mb
