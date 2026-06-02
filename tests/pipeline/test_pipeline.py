"""Tests for the Pipeline orchestrator: generate → validate → build → export.

Runs against the FakeKernel so the full spine is exercised without OCP. Schema failure
is a contract error (raises); semantic issues are data (collected in the result).
"""

import json

from ncad.pipeline.pipeline import Pipeline
from tests.kernel.fake_kernel import FakeKernel

_PARAMS = {"width": 12.0, "depth": 9.0, "num_rooms": 4, "storey_height": 3.0}


def _run(tmp_path, seed: int = 42, name: str = "house"):
    return Pipeline(FakeKernel()).run(seed=seed, params=_PARAMS, out_dir=str(tmp_path), name=name)


def test_run_produces_all_artifacts(tmp_path) -> None:
    _run(tmp_path)

    assert (tmp_path / "house.glb").exists()
    assert (tmp_path / "house.bom.json").exists()
    assert (tmp_path / "house.plan.svg").exists()
    assert (tmp_path / "house.spec.json").exists()


def test_result_reports_paths_bom_and_issues(tmp_path) -> None:
    result = _run(tmp_path)

    assert result.seed == 42
    assert result.artifacts["model"].endswith("house.glb")
    assert result.bom["door_count"] >= 1
    assert result.semantic_issues == []  # generated spec is clean


def test_persisted_spec_is_valid_json(tmp_path) -> None:
    _run(tmp_path, seed=7, name="h")

    spec = json.loads((tmp_path / "h.spec.json").read_text())
    assert spec["seed"] == 7
    assert spec["schema_version"] == 1


def test_is_deterministic(tmp_path) -> None:
    a = _run(tmp_path, seed=42, name="a")
    b = _run(tmp_path, seed=42, name="b")

    assert a.bom == b.bom
    assert (tmp_path / "a.spec.json").read_text() == (tmp_path / "b.spec.json").read_text()


def test_default_name_includes_seed(tmp_path) -> None:
    result = Pipeline(FakeKernel()).run(seed=99, params=_PARAMS, out_dir=str(tmp_path))

    assert "99" in result.name
    assert (tmp_path / f"{result.name}.glb").exists()
