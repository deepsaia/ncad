from ncad.spec.assembly_schema_validator import AssemblySchemaValidator


def _base(joints, couplings):
    return {"units": "mm", "assembly": {
        "instances": [{"id": "a", "file": "p.hocon", "part": "p"}],
        "joints": joints, "couplings": couplings}}


def _rev(jid):
    return {"id": jid, "type": "revolute",
            "between": [{"instance": "a", "connector": "c"}, {"instance": "a", "connector": "d"}]}


def test_screw_joint_with_pitch_validates() -> None:
    doc = {"units": "mm", "assembly": {
        "instances": [{"id": "a", "file": "p.hocon", "part": "p"}],
        "joints": [{"id": "s1", "type": "screw", "pitch": 2, "value": 90,
                    "between": [{"instance": "a", "connector": "c"},
                                {"instance": "a", "connector": "d"}]}]}}
    assert AssemblySchemaValidator().validate(doc) == []


def test_coupling_validates() -> None:
    doc = _base([_rev("j1"), _rev("j2")],
                [{"id": "c1", "type": "gear", "between": ["j1", "j2"], "ratio": 2}])
    assert AssemblySchemaValidator().validate(doc) == []


def test_duplicate_coupling_id_flagged() -> None:
    doc = _base([_rev("j1"), _rev("j2")],
                [{"id": "c1", "type": "gear", "between": ["j1", "j2"]},
                 {"id": "c1", "type": "belt", "between": ["j1", "j2"]}])
    assert any("duplicate coupling id" in i.message
               for i in AssemblySchemaValidator().validate(doc))


def test_coupling_referencing_missing_joint_flagged() -> None:
    doc = _base([_rev("j1")],
                [{"id": "c1", "type": "gear", "between": ["j1", "jX"]}])
    assert any("unknown joint" in i.message for i in AssemblySchemaValidator().validate(doc))


def test_coupling_id_colliding_with_joint_id_flagged() -> None:
    doc = _base([_rev("j1"), _rev("j2")],
                [{"id": "j1", "type": "gear", "between": ["j1", "j2"]}])
    assert any("collides" in i.message for i in AssemblySchemaValidator().validate(doc))
