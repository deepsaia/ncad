import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_ASM = Path(__file__).resolve().parents[2] / "examples" / "gate-5.6" / "mated_bracket.asm.hocon"


def test_gate_5_6_capstone(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = AssemblyBuilder(Build123dKernel()).assemble(str(_ASM), str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "mated_bracket.assembly.json").read_text())

    # A revolute joint with the signature that Phase 6 will drive.
    j = next(x for x in sidecar["joints"] if x["id"] == "j1")
    assert j["type"] == "revolute"
    assert j["signature"] == [{"motion": "rotation", "axis": "Z"}]

    # Interference is CORRECT: the pin passes through the bracket bore with radial clearance, so the
    # pair reads clearance (not interfering) - the pin+bore do not share volume.
    pair = next(f for f in sidecar["interference"] if {f["a"], f["b"]} == {"base", "arm"})
    assert pair["status"] == "clearance"

    # BOM: two distinct parts, quantity 1 each, both with a roll-up mass.
    items = {i["part"]: i for i in sidecar["bom"]["items"]}
    assert set(items) == {"bracket", "lever"}
    assert items["bracket"]["quantity"] == 1 and items["lever"]["quantity"] == 1
    assert sidecar["mass"]["total_mass"] > 0

    # Structured STEP AP242 written + ROUND-TRIPS as a 2-component assembly tree. (Component NAME
    # transfer through OCCT's STEP reader is version-fragile on real B-rep; the kernel-level test
    # test_kernel_export_assembly asserts names survive, so here we assert the assembly STRUCTURE.)
    step = tmp_path / "mated_bracket.step"
    assert step.is_file()
    _assert_step_assembly(str(step), expected_components=2)


def _assert_step_assembly(path: str, expected_components: int) -> None:
    """Read the STEP back via XCAF; assert it is an N-component assembly tree (not a flat blob)."""
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDF import TDF_LabelSequence
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFApp import XCAFApp_Application
    from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool

    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("XmlXCAF"))
    app.InitDocument(doc)
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    reader.ReadFile(path)
    reader.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    free = TDF_LabelSequence()
    st.GetFreeShapes(free)
    assert free.Length() == 1
    root = free.Value(1)
    assert st.IsAssembly_s(root)
    comps = TDF_LabelSequence()
    XCAFDoc_ShapeTool.GetComponents_s(root, comps)
    assert comps.Length() == expected_components
