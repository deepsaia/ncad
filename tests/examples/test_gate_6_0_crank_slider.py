import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-6.0" / "crank_slider.asm.hocon"
_R = 20.0   # crank radius (matches crank_slider.hocon: crankpin bore at x = 20)
_L = 70.0   # rod length (matches: small-end bore at x = 70 in the rod local frame)
_WRIST_LOCAL = (0.0, 0.067, 0.0)  # the piston wrist bore, local metres (modeled at y = 67 mm)


def _apply(p, m):
    return tuple(sum(p[k] * m[k][i] for k in range(3)) + m[3][i] for i in range(3))


def _wrist_y(placement):
    # The piston's wrist point in world metres -> mm; its y is the slider stroke.
    return _apply(_WRIST_LOCAL, placement)[1] * 1000.0


def test_crank_slider_motion_matches_analytic_stroke(tmp_path):
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result.get("motion") is not None
    motion = json.loads((tmp_path / "crank_slider.motion.json").read_text())
    assert len(motion["frames"]) == 73  # steps = 72 -> 73 inclusive frames

    # Declared joints + one driver reproduce the closed-form piston stroke
    # yP = R sin(theta) + sqrt(L^2 - (R cos theta)^2), with NO per-mechanism formula.
    for frame in motion["frames"]:
        theta = math.radians(frame["driver_value"])
        analytic = _R * math.sin(theta) + math.sqrt(_L ** 2 - (_R * math.cos(theta)) ** 2)
        assert math.isclose(_wrist_y(frame["placements"]["piston"]), analytic, abs_tol=0.5)


def test_crank_slider_piston_reciprocates(tmp_path):
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    motion = json.loads((tmp_path / "crank_slider.motion.json").read_text())
    ys = [_wrist_y(f["placements"]["piston"]) for f in motion["frames"]]
    # Top dead centre ~ R + L = 90, bottom ~ L - R = 50: a 40 mm stroke, peaking mid-sweep (not at
    # an endpoint), i.e. the piston rises then falls (reciprocation), not a monotonic drift.
    assert math.isclose(max(ys) - min(ys), 2.0 * _R, abs_tol=1.0)
    assert ys.index(max(ys)) not in (0, len(ys) - 1)
