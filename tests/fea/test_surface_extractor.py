from ncad.fea.surface_extractor import SurfaceExtractor

# One C3D10 tet (corner nodes 1,2,3,4; mid-side 5..10) plus two CPS6 boundary triangles gmsh would
# emit for a named surface "load". CalculiX C3D10 faces (corner triples): S1 1-2-3, S2 1-2-4,
# S3 2-3-4, S4 1-3-4. Triangle (1,2,3) -> face S1; triangle (1,2,4) -> face S2.
_MESH = """*NODE
1, 0., 0., 0.
2, 1., 0., 0.
3, 0., 1., 0.
4, 0., 0., 1.
*ELEMENT, type=C3D10, ELSET=Volume1
100, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
*ELEMENT, type=CPS6, ELSET=Surface1
200, 1, 2, 3, 5, 6, 7
201, 1, 2, 4, 5, 8, 9
*ELSET, ELSET=all
100
*ELSET, ELSET=load
200, 201
*NSET, NSET=load
1, 2, 3, 4
"""


def test_strips_2d_elements():
    result = SurfaceExtractor().rewrite(_MESH, ["load"])
    assert "CPS6" not in result["text"]
    assert "C3D10" in result["text"]      # the volume element survives


def test_emits_element_surface_for_the_group():
    result = SurfaceExtractor().rewrite(_MESH, ["load"])
    text = result["text"].upper().replace(" ", "")
    assert "*SURFACE,NAME=SLOAD,TYPE=ELEMENT" in text
    # Triangle (1,2,3) -> tet 100 face S1; triangle (1,2,4) -> face S2.
    assert "100,S1" in text and "100,S2" in text
    assert result["surfaces"]["load"] == "Sload"


def test_keeps_nset_and_volume_elset():
    result = SurfaceExtractor().rewrite(_MESH, ["load"])
    upper = result["text"].upper().replace(" ", "")
    assert "*NSET,NSET=LOAD" in upper       # node set kept for force/boundary use
    assert "*ELSET,ELSET=ALL" in upper      # the volume element set kept


def test_group_with_no_surface_triangles_reports_none():
    # A group whose ELSET is not a set of 2D triangles yields no derived surface.
    result = SurfaceExtractor().rewrite(_MESH, ["missing"])
    assert result["surfaces"]["missing"] is None
