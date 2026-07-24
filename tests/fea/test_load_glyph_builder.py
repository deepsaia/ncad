from ncad.fea.analysis_spec import AnalysisSpec
from ncad.fea.load_glyph_builder import LoadGlyphBuilder

# A 10x10 square in the z=6 plane (nodes 1-4) split into two triangles; every named group covers
# the whole square, so its centroid is the square center (5, 5, 6) and its normal is +z.
_NODES = {1: (0, 0, 6), 2: (10, 0, 6), 3: (10, 10, 6), 4: (0, 10, 6)}
_SQUARE = [(1, 2, 3), (1, 3, 4)]
_GROUP_FACES = {"tip": _SQUARE, "base": _SQUARE, "pull": _SQUARE}


def _spec(constraints, loads):
    return AnalysisSpec({"analysis": {"part": "p.hocon", "constraints": constraints,
                                      "loads": loads, "steps": []}})


def test_constraint_glyph_is_a_fixed_marker_at_the_face_centroid():
    spec = _spec([{"name": "base", "where": {"face": "bottom"}, "type": "encastre"}], [])
    glyphs = LoadGlyphBuilder().build(spec, _GROUP_FACES, _NODES)
    fixed = [g for g in glyphs if g["kind"] == "fixed"]
    assert len(fixed) == 1
    assert fixed[0]["at"] == [5.0, 5.0, 6.0]     # centroid of the (1,2,3)/base face set


def test_pressure_glyph_points_along_the_face_normal():
    spec = _spec([], [{"name": "tip", "where": {"face": "top"}, "type": "pressure",
                       "magnitude": 2.5e5}])
    glyphs = LoadGlyphBuilder().build(spec, _GROUP_FACES, _NODES)
    load = next(g for g in glyphs if g["name"] == "tip")
    assert load["kind"] == "pressure"
    assert load["at"] == [5.0, 5.0, 6.0]
    # The z=6 square's normal is +/-z; a pressure pushes INTO the face (-z here).
    assert abs(abs(load["dir"][2]) - 1.0) < 1e-9
    assert abs(load["dir"][0]) < 1e-9 and abs(load["dir"][1]) < 1e-9


def test_force_glyph_uses_the_vector_direction():
    spec = _spec([], [{"name": "pull", "where": {"face": "top"}, "type": "force",
                       "vector": [0, -500, 0]}])
    glyphs = LoadGlyphBuilder().build(spec, _GROUP_FACES, _NODES)
    load = next(g for g in glyphs if g["name"] == "pull")
    assert load["kind"] == "force"
    assert load["dir"] == [0.0, -1.0, 0.0]       # normalized vector
    assert load["magnitude"] == 500.0


def test_gravity_glyph_uses_its_direction_and_the_model_center():
    spec = _spec([], [{"name": "w", "type": "gravity", "g": 9.81, "direction": [0, 0, -1]}])
    glyphs = LoadGlyphBuilder().build(spec, _GROUP_FACES, _NODES)
    load = next(g for g in glyphs if g["name"] == "w")
    assert load["kind"] == "gravity" and load["dir"] == [0.0, 0.0, -1.0]


def test_thermal_flux_glyph_from_nested_step_loads():
    spec_with_heat = AnalysisSpec({"analysis": {"part": "p.hocon", "constraints": [], "loads": [],
        "steps": [{"name": "heat", "procedure": "heat_transfer",
                   "loads": [{"name": "tip", "where": {"face": "top"}, "type": "flux",
                              "magnitude": 500}]}]}})
    glyphs = LoadGlyphBuilder().build(spec_with_heat, _GROUP_FACES, _NODES)
    assert any(g["kind"] == "flux" and g["name"] == "tip" for g in glyphs)
