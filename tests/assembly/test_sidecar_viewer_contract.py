import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-5.4a" / "pinned_lever.asm.hocon"


def test_sidecar_exposes_connectors_and_joint_refs(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    sidecar = json.loads((tmp_path / "pinned_lever.assembly.json").read_text())

    # Every instance exposes world-space connector frames with a full origin + triad (the anchor +
    # orientation the viewer's joint glyphs and connector gizmos read).
    by_instance = {}
    for inst in sidecar["instances"]:
        for c in inst.get("connectors", []):
            assert set(c) >= {"id", "origin", "x", "y", "z"}
            assert len(c["origin"]) == 3 and len(c["z"]) == 3
            by_instance.setdefault(inst["id"], {})[c["id"]] = c

    # Every joint `between` ref resolves to an emitted connector frame, so the glyph overlay can
    # anchor each joint (it looks up between[0] -> that instance's connector).
    assert sidecar["joints"], "gate-5.4a should carry at least one joint"
    for joint in sidecar["joints"]:
        for ref in joint["between"]:
            assert ref["connector"] in by_instance.get(ref["instance"], {}), (
                f"joint {joint['id']} ref {ref} has no emitted connector frame")
