"""ModelCatalog analysis discovery: .analysis.json names/labels + safe sidecar resolution."""

import json
from pathlib import Path

from ncad.viewer.model_catalog import ModelCatalog


def _analysis(root: Path, name: str, summary: dict, source: str | None = None,
              mesh: bool = False) -> Path:
    """Create out/analyses/<name>/<name>.analysis.json (+ optional mesh sidecar)."""
    d = root / "analyses" / name
    d.mkdir(parents=True, exist_ok=True)
    doc: dict = {"summary": summary}
    if source is not None:
        doc["source"] = source
    (d / f"{name}.analysis.json").write_text(json.dumps(doc))
    if mesh:
        (d / f"{name}.analysis.mesh.json").write_text("{}")
    return d


def test_lists_analysis_names(tmp_path):
    _analysis(tmp_path, "bracket", {}, mesh=True)   # mesh sidecar is NOT a separate analysis
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.analysis_names() == ["bracket"]


def test_analysis_label_is_max_von_mises(tmp_path):
    _analysis(tmp_path, "bracket", {"max_von_mises": 423646.0})
    labels = {a["name"]: a["label"] for a in ModelCatalog(str(tmp_path)).analyses_with_labels()}
    assert labels["bracket"] is not None and "Pa" in labels["bracket"]


def test_resolve_analysis_and_mesh(tmp_path):
    _analysis(tmp_path, "bracket", {}, mesh=True)
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_analysis("bracket").endswith("/analyses/bracket/bracket.analysis.json")
    assert catalog.resolve_analysis_mesh("bracket").endswith(
        "/analyses/bracket/bracket.analysis.mesh.json")
    assert catalog.resolve_analysis("missing") is None


def test_resolve_analysis_rejects_traversal(tmp_path):
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_analysis("../evil") is None


def test_analyses_with_labels_carries_source(tmp_path):
    _analysis(tmp_path, "bracket", {}, source="/x/bracket.analysis.hocon")
    row = next(a for a in ModelCatalog(str(tmp_path)).analyses_with_labels()
               if a["name"] == "bracket")
    assert row["source"] == "/x/bracket.analysis.hocon"
