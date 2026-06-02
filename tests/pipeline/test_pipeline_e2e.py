"""Slow end-to-end test of the full spine with the real build123d kernel.

This is the Phase 5 milestone gate: a single seed flows through
generate → validate → build → export and yields a real glTF/STEP-capable model plus
BOM, plan, and spec — with no schema or semantic issues. Marked ``slow`` (OCP import).
"""

import json

import pytest

pytestmark = pytest.mark.slow


def test_full_spine_produces_clean_artifacts(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.pipeline.pipeline import Pipeline

    params = {"width": 12.0, "depth": 9.0, "num_rooms": 4, "storey_height": 3.0}
    result = Pipeline(Build123dKernel()).run(
        seed=42, params=params, out_dir=str(tmp_path), name="gate"
    )

    # All artifacts exist and are non-empty.
    for kind in ("model", "bom", "plan", "spec"):
        path = tmp_path / {
            "model": "gate.glb",
            "bom": "gate.bom.json",
            "plan": "gate.plan.svg",
            "spec": "gate.spec.json",
        }[kind]
        assert path.exists() and path.stat().st_size > 0, f"{kind} missing/empty"

    # The spine produced a clean building.
    assert result.semantic_issues == []
    assert result.bom["floor_area"] == pytest.approx(108.0)

    # The glb is a real binary glTF container.
    assert (tmp_path / "gate.glb").read_bytes()[:4] == b"glTF"

    # The persisted spec round-trips.
    spec = json.loads((tmp_path / "gate.spec.json").read_text())
    assert spec["seed"] == 42
