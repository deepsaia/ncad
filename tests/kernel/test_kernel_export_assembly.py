import pytest

pytestmark = pytest.mark.slow

_ID = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _at(x):
    return [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [x, 0, 0, 1]]


def test_export_assembly_round_trips_structure(tmp_path) -> None:
    from build123d import Box

    from ncad.kernel.build123d_kernel import Build123dKernel
    # DISTINCT geometry per part (identical parts get deduped on read).
    comps = [
        {"shape": Box(10, 10, 10), "name": "bracket", "color": (0.8, 0.2, 0.2),
         "material": "steel", "placement": _ID},
        {"shape": Box(20, 8, 8), "name": "lever", "color": (0.2, 0.4, 0.9),
         "material": "alu", "placement": _at(40)},
    ]
    path = str(tmp_path / "asm.step")
    Build123dKernel().export_assembly(comps, path)

    # Read back via XCAF and assert the assembly tree + names survived.
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDF import TDF_Label, TDF_LabelSequence
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
    comps_seq = TDF_LabelSequence()
    XCAFDoc_ShapeTool.GetComponents_s(root, comps_seq)
    assert comps_seq.Length() == 2
    names = set()
    for i in range(1, comps_seq.Length() + 1):
        ref = TDF_Label()
        XCAFDoc_ShapeTool.GetReferredShape_s(comps_seq.Value(i), ref)
        nm = TDataStd_Name()
        if ref.FindAttribute(TDataStd_Name.GetID_s(), nm):
            names.add(nm.Get().ToExtString())
    assert names == {"bracket", "lever"}
