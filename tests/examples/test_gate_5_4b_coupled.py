import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-5.4b" / "geared_screw.asm.hocon"


def test_gate_5_4b_screw_and_coupling(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "geared_screw.assembly.json").read_text())
    # The screw is fully shipped: coaxial + a pitch-bearing signature; its valued depth solves.
    screw = next(j for j in sidecar["joints"] if j["id"] == "screw1")
    assert screw["type"] == "screw"
    assert screw["signature"][0]["motion"] == "screw"
    assert screw["signature"][0]["pitch"] == 4
    # The two gears sit on parallel offset shafts (a real mesh), coupled by the declared gear ratio.
    mesh = next(c for c in sidecar["couplings"] if c["id"] == "mesh")
    assert mesh["type"] == "gear" and mesh["between"] == ["jA", "jB"] and mesh["ratio"] == 2
    assert "declared coupling" in sidecar["solve"]["explanation"]
    # The mate network is well-posed (no spurious redundancy from shared axes, no failures).
    assert not sidecar["solve"]["failing_ids"]
