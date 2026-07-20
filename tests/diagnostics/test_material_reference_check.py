from ncad.diagnostics import codes
from ncad.diagnostics.checks.material_reference_check import MaterialReferenceCheck

# Known materials the caller resolved (seed + inline + external), passed in like connectors_by_part.
_KNOWN = {"steel_1018", "oak", "glass"}


def _doc(parts):
    return {"parts": parts}


def test_resolved_materials_yield_nothing():
    doc = _doc({"beam": {"material": "steel_1018", "features": [
        {"id": "sk", "op": "sketch"}, {"id": "e", "op": "extrude", "material": "oak"}]}})
    assert MaterialReferenceCheck().check(doc, _KNOWN) == []


def test_unknown_part_material_flagged():
    doc = _doc({"beam": {"material": "alumnium_6061", "features": []}})
    diags = MaterialReferenceCheck().check(doc, _KNOWN)
    assert [d.code for d in diags] == [codes.UNKNOWN_REFERENCE]
    d = diags[0]
    assert d.severity == "error" and d.stage == "semantic"
    assert "alumnium_6061" in d.message
    assert d.location == "parts.beam.material"


def test_unknown_feature_material_override_flagged():
    doc = _doc({"beam": {"material": "oak", "features": [
        {"id": "rail", "op": "primitive", "material": "raling"}]}})
    diags = MaterialReferenceCheck().check(doc, _KNOWN)
    assert [d.code for d in diags] == [codes.UNKNOWN_REFERENCE]
    assert "raling" in diags[0].message
    assert diags[0].location == "parts.beam.features.0.material"


def test_missing_material_is_not_flagged():
    # A part with no material declared is valid (a body may inherit a default / stay uncolored).
    doc = _doc({"beam": {"features": [{"id": "sk", "op": "sketch"}]}})
    assert MaterialReferenceCheck().check(doc, _KNOWN) == []


def test_multiple_unknowns_each_flagged():
    doc = _doc({
        "beam": {"material": "nope1", "features": []},
        "plate": {"material": "steel_1018", "features": [
            {"id": "f", "op": "extrude", "material": "nope2"}]}})
    diags = MaterialReferenceCheck().check(doc, _KNOWN)
    assert len(diags) == 2
    assert {"nope1", "nope2"} <= {m for d in diags for m in [d.message]} or \
        all(any(n in d.message for d in diags) for n in ("nope1", "nope2"))


def test_no_parts_block_yields_nothing():
    assert MaterialReferenceCheck().check({}, _KNOWN) == []
