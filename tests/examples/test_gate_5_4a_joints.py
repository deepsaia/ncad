import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-5.4a" / "pinned_lever.asm.hocon"


def test_gate_5_4a_revolute_joint(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "pinned_lever.assembly.json").read_text())
    joints = sidecar["joints"]
    assert [j["id"] for j in joints] == ["j1"]
    assert joints[0]["type"] == "revolute"
    assert joints[0]["signature"] == [{"motion": "rotation", "axis": "Z"}]
    assert joints[0]["ok"] is True
    # A valueless revolute leaves a free rotational DoF: the solve is not fully rigid.
    assert sidecar["solve"]["dof"] > 0
