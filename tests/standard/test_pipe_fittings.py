"""The pipe_fitting grouped family generates elbow/tee/reducer by designation + custom dims."""

import pytest

from ncad.standard import StandardLibrary


def test_pipe_fitting_is_a_grouped_family():
    lib = StandardLibrary()
    assert "pipe_fitting" in lib.families()
    assert set(lib.subtypes("pipe_fitting")) == {"elbow", "tee", "reducer"}
    assert lib.subtypes("washer") == []  # a flat family has no subtypes


def test_elbow_document_shape():
    doc = StandardLibrary().generate("pipe_fitting", "DN50", subtype="elbow")
    part = doc["parts"]["pipe_fitting_elbow_dn50"]
    ops = [f["op"] for f in part["features"]]
    # two circle profiles, a 3D centerline, two sweeps, and a bore cut.
    assert ops == ["sketch", "sketch", "path3d", "sweep", "sweep", "boolean"]


def test_tee_document_shape():
    doc = StandardLibrary().generate("pipe_fitting", "DN50", subtype="tee")
    ops = [f["op"] for f in doc["parts"]["pipe_fitting_tee_dn50"]["features"]]
    # run + branch outer, union, run + branch bore, two cuts.
    assert ops == ["primitive", "primitive", "boolean", "primitive", "primitive",
                   "boolean", "boolean"]


def test_reducer_document_shape():
    doc = StandardLibrary().generate("pipe_fitting", "DN80xDN50", subtype="reducer")
    ops = [f["op"] for f in doc["parts"]["pipe_fitting_reducer_dn80xdn50"]["features"]]
    # two outer circles lofted, two inner circles lofted, cut.
    assert ops == ["sketch", "sketch", "loft", "sketch", "sketch", "loft", "boolean"]


def test_grouped_family_needs_a_subtype():
    with pytest.raises(KeyError, match="needs a subtype"):
        StandardLibrary().generate("pipe_fitting", "DN50")


def test_unknown_subtype_raises():
    with pytest.raises(KeyError, match="unknown pipe_fitting subtype"):
        StandardLibrary().generate("pipe_fitting", "DN50", subtype="cross")


def test_flat_family_rejects_a_subtype():
    with pytest.raises(KeyError, match="takes no subtype"):
        StandardLibrary().generate("washer", "M8", subtype="elbow")


def test_custom_elbow_dimensions():
    doc = StandardLibrary().generate_custom(
        "pipe_fitting",
        {"outer_diameter": 60.0, "wall_thickness": 4.0, "bend_radius": 90.0},
        subtype="elbow")
    assert "pipe_fitting_elbow_custom" in doc["parts"]


def test_custom_missing_dimension_raises():
    with pytest.raises(ValueError, match="missing"):
        StandardLibrary().generate_custom(
            "pipe_fitting", {"outer_diameter": 60.0}, subtype="tee")


def test_provenance_per_subtype():
    prov = StandardLibrary().provenance("pipe_fitting", subtype="reducer")
    assert "B16.9" in prov["standard"]
    assert prov["version"] and prov["source"]
