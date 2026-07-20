from ncad.diagnostics import codes
from ncad.diagnostics.checks.disconnected_solid_check import DisconnectedSolidCheck


def test_single_body_yields_nothing():
    assert DisconnectedSolidCheck().check("bracket", 1) == []


def test_zero_body_yields_nothing():
    # A part that did not build (0 bodies) is handled elsewhere; the check only reports >1.
    assert DisconnectedSolidCheck().check("bracket", 0) == []


def test_multiple_disjoint_bodies_reported_as_info():
    diags = DisconnectedSolidCheck().check("stand", 3)
    assert len(diags) == 1
    d = diags[0]
    assert d.code == codes.DISCONNECTED_SOLID
    assert d.severity == "info"          # never blocks; makes no judgment about intent
    assert d.stage == "build"
    assert d.location == "parts.stand"
    assert "3 disjoint solids" in d.message
