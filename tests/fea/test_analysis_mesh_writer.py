from ncad.fea.analysis_mesh_writer import AnalysisMeshWriter

# Two tets sharing face (2,3,4); the shared face is interior (appears twice) -> excluded.
# Tet A corners 1,2,3,4; Tet B corners 2,3,4,5.
_NODES = {1: (0, 0, 0), 2: (1, 0, 0), 3: (0, 1, 0), 4: (0, 0, 1), 5: (1, 1, 1)}
_ELEMENTS = [[1, 2, 3, 4], [2, 3, 4, 5]]
_FIELDS = {"von_mises": {1: 10.0, 2: 20.0, 3: 30.0, 4: 40.0, 5: 50.0}}


def test_boundary_excludes_shared_interior_face():
    mesh = AnalysisMeshWriter().build(_NODES, _ELEMENTS, _FIELDS)
    # 2 tets * 4 faces = 8; the shared (2,3,4) appears twice -> 6 boundary triangles.
    assert len(mesh["triangles"]) == 6


def test_points_and_field_aligned():
    mesh = AnalysisMeshWriter().build(_NODES, _ELEMENTS, _FIELDS)
    assert len(mesh["points"]) == len(mesh["fields"]["von_mises"])
    assert mesh["ranges"]["von_mises"] == [10.0, 50.0]


def test_triangles_index_into_points():
    mesh = AnalysisMeshWriter().build(_NODES, _ELEMENTS, _FIELDS)
    n = len(mesh["points"])
    assert all(0 <= i < n for tri in mesh["triangles"] for i in tri)


def test_absent_field_is_omitted():
    mesh = AnalysisMeshWriter().build(_NODES, _ELEMENTS, {})
    assert mesh["fields"] == {} and mesh["ranges"] == {}
