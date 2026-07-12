import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-5.1" / "connected_stack.asm.hocon"


def test_gate_5_1_connect_snaps_peg_onto_plate(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "connected_stack.assembly.json").read_text())
    ids = [i["id"] for i in sidecar["instances"]]
    assert ids == ["base", "pin"]
    pin = next(i for i in sidecar["instances"] if i["id"] == "pin")
    # The peg's base connector snapped onto the plate top (z=6mm = 0.006m).
    assert pin["placement"][3][2] == pytest.approx(0.006, abs=1e-6)
    # World-space connector frames are emitted for the viewer overlay.
    assert any(c["id"] == "base" for c in pin["connectors"])
    base = next(i for i in sidecar["instances"] if i["id"] == "base")
    assert any(c["id"] == "top" for c in base["connectors"])
