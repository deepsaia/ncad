import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-5.7" / "caster.asm.hocon"


def test_gate_5_7_caster(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "caster.assembly.json").read_text())

    ids = {i["id"] for i in sidecar["instances"]}
    # Nested sub-assembly instances are namespaced under the swivel instance.
    assert {"swivel/axle", "swivel/wheel"} <= ids
    # Four mounting bolts are component-patterned into ordinal instances.
    assert {"bolt/0", "bolt/1", "bolt/2", "bolt/3"} <= ids
    # The tangent mate seating the stop is active/ok.
    assert any(m["id"] == "seatStop" and m["ok"] for m in sidecar["mates"])
    # BOM + roll-up mass present, interference computed, structured STEP written.
    assert sidecar["bom"]["items"] and sidecar["mass"]["total_mass"] > 0
    assert isinstance(sidecar["interference"], list)
    assert (tmp_path / "caster.step").is_file()
    # The parts are laid out clash-free: no pair of parts interferes (the reported interference is
    # only touching/clearance). A patterned bolt landing on top of another, or the fork punching the
    # wheel, would show up here.
    assert not [f for f in sidecar["interference"] if f["status"] == "interfering"], \
        [f for f in sidecar["interference"] if f["status"] == "interfering"]


def test_gate_5_7_wheel_axle_sub_assembly_spins() -> None:
    import tempfile

    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    child = _ASM.parent / "wheel_axle.asm.hocon"
    out = tempfile.mkdtemp()
    result = AssemblyBuilder(Build123dKernel()).assemble(str(child), out)
    assert not result["issues"], result["issues"]
    sidecar = json.loads((Path(out) / "wheel_axle.assembly.json").read_text())
    # The wheel is pinned to the axle by a revolute (one rotational DoF, driven in Phase 6).
    spin = next(j for j in sidecar["joints"] if j["id"] == "spin")
    assert spin["type"] == "revolute"
    assert spin["signature"] == [{"motion": "rotation", "axis": "Z"}]
