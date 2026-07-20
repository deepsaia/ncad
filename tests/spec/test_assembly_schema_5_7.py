"""Acceptance matrix for the bucket 5.7 assembly-schema additions.

Every 5.7 addition (assembly instances, component pattern/mirror/replace, tangent/symmetric/width
mates, cam coupling) has an accept case (valid document -> no issues) and, where semantic, a
reject case (invalid document -> id-attributed issue).
"""

from ncad.spec.assembly_schema_validator import AssemblySchemaValidator


def _asm(instances, **extra) -> dict:
    assembly = {"instances": instances, **extra}
    return {"units": "mm", "assembly": assembly}


def _validate(document: dict):
    return AssemblySchemaValidator().validate(document)


def test_accept_sub_assembly_instance() -> None:
    doc = _asm([{"id": "sub", "assembly": "child.asm.hocon"}])
    assert _validate(doc) == []


def test_accept_pattern_instance() -> None:
    doc = _asm([{"id": "b", "file": "p.hocon", "part": "bolt",
                 "pattern": {"kind": "circular", "count": 4,
                             "axis": {"point": [0, 0, 0], "dir": [0, 0, 1]}}}])
    assert _validate(doc) == []


def test_accept_mirror_instance() -> None:
    doc = _asm([{"id": "left", "file": "p.hocon", "part": "bracket"},
                {"id": "right", "of": "left", "mirror": {"plane": "YZ"}}])
    assert _validate(doc) == []


def test_accept_replace_instance() -> None:
    doc = _asm([{"id": "bolt", "file": "p.hocon", "part": "bolt",
                 "replace": {"file": "p8.hocon", "part": "bolt"}}])
    assert _validate(doc) == []


def test_accept_tangent_mate() -> None:
    doc = _asm(
        [{"id": "a", "file": "p.hocon", "part": "pin"},
         {"id": "b", "file": "p.hocon", "part": "plate"}],
        constraints=[{"id": "t", "type": "tangent", "between": [
            {"instance": "a", "connector": "shaft"},
            {"instance": "b", "connector": "face"}]}])
    assert _validate(doc) == []


def test_accept_symmetric_mate_with_three_refs() -> None:
    doc = _asm(
        [{"id": "a", "file": "p.hocon", "part": "x"},
         {"id": "b", "file": "p.hocon", "part": "x"},
         {"id": "c", "file": "p.hocon", "part": "x"}],
        constraints=[{"id": "s", "type": "symmetric", "between": [
            {"instance": "a", "connector": "f"},
            {"instance": "b", "connector": "f"},
            {"instance": "c", "connector": "mid"}]}])
    assert _validate(doc) == []


def test_accept_width_mate() -> None:
    doc = _asm(
        [{"id": "a", "file": "p.hocon", "part": "x"},
         {"id": "b", "file": "p.hocon", "part": "x"},
         {"id": "c", "file": "p.hocon", "part": "x"}],
        constraints=[{"id": "w", "type": "width", "between": [
            {"instance": "a", "connector": "f"},
            {"instance": "b", "connector": "left"},
            {"instance": "c", "connector": "right"}]}])
    assert _validate(doc) == []


def test_accept_cam_coupling() -> None:
    doc = _asm(
        [{"id": "a", "file": "p.hocon", "part": "x"},
         {"id": "b", "file": "p.hocon", "part": "x"}],
        joints=[
            {"id": "jc", "type": "revolute", "between": [
                {"instance": "a", "connector": "ax"}, {"instance": "b", "connector": "ax"}]},
            {"id": "jf", "type": "revolute", "between": [
                {"instance": "a", "connector": "ax"}, {"instance": "b", "connector": "ax"}]}],
        couplings=[{"id": "cam1", "type": "cam", "between": ["jc", "jf"],
                    "profile": "select edges where type='bspline'"}])
    assert _validate(doc) == []


def test_reject_unknown_mate_type() -> None:
    doc = _asm(
        [{"id": "a", "file": "p.hocon", "part": "x"}],
        constraints=[{"id": "m", "type": "welded", "between": [
            {"instance": "a", "connector": "f"}]}])
    assert _validate(doc)


def test_reject_cam_coupling_unknown_joint() -> None:
    doc = _asm(
        [{"id": "a", "file": "p.hocon", "part": "x"}],
        couplings=[{"id": "cam1", "type": "cam", "between": ["nope1", "nope2"]}])
    issues = _validate(doc)
    assert any("unknown joint" in i.message for i in issues)


def test_reject_instance_with_no_geometry_source() -> None:
    doc = _asm([{"id": "orphan"}])
    issues = _validate(doc)
    assert any("geometry source" in i.message for i in issues)


def test_reject_instance_partial_part_ref() -> None:
    doc = _asm([{"id": "a", "file": "p.hocon"}])  # file without part
    issues = _validate(doc)
    assert any("both 'file' and 'part'" in i.message for i in issues)
