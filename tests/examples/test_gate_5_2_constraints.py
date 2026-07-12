import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-5.2" / "arm_linkage.asm.hocon"


def test_gate_5_2_mate_network_solves(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "arm_linkage.assembly.json").read_text())
    assert sidecar["solve"]["status"] in ("well_constrained", "under_constrained", "redundant")
    assert not sidecar["solve"]["failing_ids"]
    ids = {m["id"] for m in sidecar["mates"]}
    assert ids == {"m1", "m2"}
    assert all(m["ok"] for m in sidecar["mates"])
    # The lever's bottom connector coincides with the bracket top (z=6mm=0.006m): the solved arm
    # sits on the bracket, coaxial with the pivot.
    arm = next(i for i in sidecar["instances"] if i["id"] == "arm")
    assert arm["placement"][3][2] == pytest.approx(0.006, abs=1e-4)
