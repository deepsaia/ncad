import pytest

from ncad.fea.analysis_error import AnalysisError
from ncad.fea.analysis_spec import AnalysisSpec
from ncad.fea.deck_writer import DeckWriter

# A tiny mesh .inp stand-in with the named sets GmshMesher would write.
_MESH_INP = """*NODE
1, 0., 0., 0.
2, 1., 0., 0.
*ELEMENT, type=C3D10, ELSET=all
1, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2
*ELSET, ELSET=base
1
*NSET, NSET=base
1, 2
*NSET, NSET=tip
2
"""

_STEEL = {"structural": {"youngs_modulus": 200e9, "poisson": 0.29, "yield": 370e6},
          "physical": {"density": 7870}, "thermal": {"conductivity": 51.9}}


def _spec(steps, loads=None, constraints=None):
    return AnalysisSpec({"analysis": {
        "part": "p.hocon",
        "constraints": constraints or [{"name": "base", "where": {"face": "bottom"},
                                        "type": "encastre"}],
        "loads": loads or [{"name": "tip", "where": {"face": "top"}, "type": "force",
                            "vector": [0, -500, 0]}],
        "steps": steps}})


def test_deck_has_material_section_and_static_step():
    spec = _spec([{"name": "stress", "procedure": "static"}])
    deck = DeckWriter().write(_MESH_INP, spec, _STEEL)
    upper = deck.upper()
    assert "*MATERIAL" in upper
    assert "*ELASTIC" in upper
    assert "*SOLID SECTION" in upper and "ELSET=ALL" in upper.replace(" ", "")
    assert "*STEP" in upper and "*STATIC" in upper and "*END STEP" in upper


def test_static_step_writes_boundary_and_cload():
    spec = _spec([{"name": "stress", "procedure": "static"}])
    deck = DeckWriter().write(_MESH_INP, spec, _STEEL).upper()
    assert "*BOUNDARY" in deck                       # the encastre constraint
    assert "*CLOAD" in deck                          # the force load
    assert "BASE" in deck and "TIP" in deck          # references the named sets


def test_frequency_step_writes_eigenvalue_request():
    spec = _spec([{"name": "modes", "procedure": "frequency", "eigenvalues": 6}])
    deck = DeckWriter().write(_MESH_INP, spec, _STEEL).upper()
    assert "*FREQUENCY" in deck and "6" in deck


def test_heat_transfer_without_conductivity_raises():
    steel_no_k = {"structural": {"youngs_modulus": 200e9, "poisson": 0.29},
                  "physical": {"density": 7870}}
    spec = _spec([{"name": "heat", "procedure": "heat_transfer",
                   "loads": [{"name": "in", "where": {"face": "top"},
                              "type": "flux", "magnitude": 500}]}])
    with pytest.raises(AnalysisError):
        DeckWriter().write(_MESH_INP, spec, steel_no_k)


def test_heat_transfer_writes_conductivity_and_flux():
    spec = _spec([{"name": "heat", "procedure": "heat_transfer",
                   "loads": [{"name": "in", "where": {"face": "top"},
                              "type": "flux", "magnitude": 500}]}])
    deck = DeckWriter().write(_MESH_INP, spec, _STEEL).upper()
    assert "*CONDUCTIVITY" in deck and "*HEAT TRANSFER" in deck and "*DFLUX" in deck


def test_pressure_uses_derived_surface_name():
    # A pressure load references its derived *SURFACE (from SurfaceExtractor), not the raw group.
    spec = _spec([{"name": "stress", "procedure": "static"}],
                 loads=[{"name": "tip", "where": {"face": "top"}, "type": "pressure",
                         "magnitude": 2.5e5}])
    deck = DeckWriter().write(_MESH_INP, spec, _STEEL, surfaces={"tip": "Stip"})
    assert "*DSLOAD" in deck.upper()
    assert "Stip, P" in deck
