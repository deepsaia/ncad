"""ModelCatalog analysis discovery: .analysis.json names/labels + safe sidecar resolution."""

import json

from ncad.viewer.model_catalog import ModelCatalog


def test_lists_analysis_names(tmp_path):
    (tmp_path / "bracket.analysis.json").write_text(json.dumps({"summary": {}}))
    (tmp_path / "bracket.analysis.mesh.json").write_text("{}")   # sidecar, NOT a separate analysis
    (tmp_path / "part.glb").write_bytes(b"\x00")                 # not an analysis
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.analysis_names() == ["bracket"]


def test_analysis_label_is_max_von_mises(tmp_path):
    (tmp_path / "bracket.analysis.json").write_text(
        json.dumps({"summary": {"max_von_mises": 423646.0}}))
    labels = {a["name"]: a["label"] for a in ModelCatalog(str(tmp_path)).analyses_with_labels()}
    assert labels["bracket"] is not None and "Pa" in labels["bracket"]


def test_resolve_analysis_and_mesh(tmp_path):
    (tmp_path / "bracket.analysis.json").write_text("{}")
    (tmp_path / "bracket.analysis.mesh.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_analysis("bracket").endswith("bracket.analysis.json")
    assert catalog.resolve_analysis_mesh("bracket").endswith("bracket.analysis.mesh.json")
    assert catalog.resolve_analysis("missing") is None


def test_resolve_analysis_rejects_traversal(tmp_path):
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_analysis("../evil") is None


def test_analyses_with_labels_carries_source(tmp_path):
    (tmp_path / "bracket.analysis.json").write_text(
        json.dumps({"summary": {}, "source": "/x/bracket.analysis.hocon"}))
    row = next(a for a in ModelCatalog(str(tmp_path)).analyses_with_labels()
               if a["name"] == "bracket")
    assert row["source"] == "/x/bracket.analysis.hocon"
