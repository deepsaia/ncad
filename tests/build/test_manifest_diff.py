"""ManifestDiff flips only the layers that actually changed between two geometry-facts manifests."""

import copy

from ncad.build.manifest_diff import ManifestDiff


def _manifest():
    return {
        "bbox": {"min": [0, 0, 0], "max": [20, 10, 6], "size": [20, 10, 6],
                 "center": [10, 5, 3]},
        "counts": {"solids": 1, "faces": 6, "edges": 12},
        "bodies": [{"id": "body/0", "volume": 1200.0, "centroid": [10, 5, 3]}],
    }


def test_identical_manifests_report_no_change():
    d = ManifestDiff().diff(_manifest(), _manifest())
    assert d == {"topology_changed": False, "geometry_changed": False,
                 "bbox_changed": False, "count_delta": {}}


def test_moved_body_flips_only_geometry():
    old = _manifest()
    new = copy.deepcopy(old)
    new["bodies"][0]["centroid"] = [12, 5, 3]   # translated, same topology + same bbox size
    new["bbox"] = old["bbox"]                    # bbox size unchanged
    d = ManifestDiff().diff(old, new)
    assert d["geometry_changed"] is True
    assert d["topology_changed"] is False
    assert d["bbox_changed"] is False


def test_new_face_flips_topology_and_reports_count_delta():
    old = _manifest()
    new = copy.deepcopy(old)
    new["counts"]["faces"] = 7                   # a face appeared (e.g. a chamfer)
    d = ManifestDiff().diff(old, new)
    assert d["topology_changed"] is True
    assert d["count_delta"] == {"faces": 1}


def test_body_split_flips_topology_via_body_ids():
    old = _manifest()
    new = copy.deepcopy(old)
    new["counts"]["solids"] = 2
    new["bodies"].append({"id": "body/1", "volume": 500.0, "centroid": [40, 5, 3]})
    d = ManifestDiff().diff(old, new)
    assert d["topology_changed"] is True
    assert d["count_delta"] == {"solids": 1}


def test_resize_flips_bbox_and_geometry_not_topology():
    old = _manifest()
    new = copy.deepcopy(old)
    new["bbox"]["max"] = [40, 10, 6]
    new["bbox"]["size"] = [40, 10, 6]
    new["bodies"][0]["volume"] = 2400.0
    new["bodies"][0]["centroid"] = [20, 5, 3]
    d = ManifestDiff().diff(old, new)
    assert d["bbox_changed"] is True
    assert d["geometry_changed"] is True
    assert d["topology_changed"] is False


def test_float_noise_below_tolerance_does_not_churn():
    old = _manifest()
    new = copy.deepcopy(old)
    new["bodies"][0]["volume"] = 1200.0 + 1e-9    # sub-tolerance jitter
    new["bbox"]["max"] = [20 + 1e-9, 10, 6]
    d = ManifestDiff().diff(old, new)
    assert d["geometry_changed"] is False
    assert d["bbox_changed"] is False
