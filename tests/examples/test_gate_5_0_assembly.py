import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-5.0" / "pegged_plate.asm.hocon"


def test_gate_5_0_assembly_composes(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "pegged_plate.assembly.json").read_text())
    ids = [i["id"] for i in sidecar["instances"]]
    assert ids == ["base", "peg_a", "peg_b"]
    # plate.glb + peg.glb: two distinct part glbs (base uses plate, both pegs share peg).
    glbs = {i["part_glb"] for i in sidecar["instances"]}
    assert len(glbs) == 2
    # Pegs are placed in the plate's centered frame (origin = part center): inset on the top face.
    peg_a = next(i for i in sidecar["instances"] if i["id"] == "peg_a")
    assert peg_a["placement"][3][0] == -15 and peg_a["placement"][3][1] == 8
    assert peg_a["placement"][3][2] == 6  # on the plate top (z=6)
