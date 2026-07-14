from ncad.sketch.edge_projector import EdgeProjector


def test_line_becomes_construction_line_with_points():
    ents, degen = EdgeProjector().project(
        [{"kind": "line", "points": [(0.0, 0.0), (10.0, 0.0)]}])
    assert degen == 0
    lines = [e for e in ents if e["type"] == "line"]
    points = [e for e in ents if e["type"] == "point"]
    assert len(lines) == 1 and len(points) == 2
    assert all(e.get("construction") is True for e in ents)


def test_circle_becomes_construction_circle():
    ents, degen = EdgeProjector().project(
        [{"kind": "circle", "center": (1.0, 2.0), "radius": 5.0}])
    circles = [e for e in ents if e["type"] == "circle"]
    assert len(circles) == 1 and circles[0]["radius"] == 5.0
    assert all(e.get("construction") is True for e in ents)


def test_spline_becomes_interpolated_construction_curve():
    pts = [(0.0, 0.0), (5.0, 3.0), (10.0, 0.0)]
    ents, degen = EdgeProjector().project([{"kind": "spline", "points": pts}])
    assert degen == 0
    curves = [e for e in ents if e["type"] == "interpolated"]
    points = [e for e in ents if e["type"] == "point"]
    assert len(curves) == 1 and len(points) == len(pts)
    # The curve references the point ids in order, and all entities are construction geometry.
    assert curves[0]["points"] == [p["id"] for p in points]
    assert all(e.get("construction") is True for e in ents)


def test_bezier_projection_becomes_bezier_construction_curve():
    pts = [(0.0, 0.0), (5.0, 3.0), (10.0, 0.0)]
    ents, _ = EdgeProjector().project([{"kind": "bezier", "points": pts}])
    curves = [e for e in ents if e["type"] == "bezier"]
    assert len(curves) == 1
    assert all(e.get("construction") is True for e in ents)


def test_degenerate_edges_are_skipped_and_counted():
    ents, degen = EdgeProjector().project([
        {"kind": "line", "points": [(0.0, 0.0), (10.0, 0.0)]},
        {"kind": "degenerate"},
    ])
    assert degen == 1
    assert [e for e in ents if e["type"] == "line"]


def test_ids_are_padded_for_many_edges():
    descriptors = [{"kind": "line", "points": [(float(i), 0.0), (float(i), 1.0)]}
                   for i in range(11)]
    ents, _ = EdgeProjector().project(descriptors)
    line_ids = sorted(e["id"] for e in ents if e["type"] == "line")
    assert line_ids == sorted(line_ids)
    assert any("/00" in i for i in line_ids)
