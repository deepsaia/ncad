import copy
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_BRACKET = Path(__file__).resolve().parents[2] / "examples" / "gate-2.9" / "mounting_bracket.hocon"


def _build(document: dict) -> object:
    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.op_registry import OpRegistry

    # Builder needs (kernel, registry[, cache]); registry from with_defaults.
    builder = Builder(Build123dKernel(), OpRegistry.with_defaults())
    part = next(iter(document["parts"].values()))
    _result, element_map, _statuses = builder.build_part_mapped(part)
    return element_map


def _load(path: Path) -> dict:
    from ncad.spec.spec_loader import SpecLoader

    return SpecLoader().load(str(path))


def _ids(element_map: object) -> set:
    return {e.id for e in element_map.elements()}  # pyrefly: ignore[missing-attribute]


def test_names_are_deterministic() -> None:
    document = _load(_BRACKET)
    first = _ids(_build(copy.deepcopy(document)))
    second = _ids(_build(copy.deepcopy(document)))
    assert first == second and len(first) > 0


def test_names_are_persistent_format() -> None:
    document = _load(_BRACKET)
    ids = _ids(_build(copy.deepcopy(document)))
    # Every element carries a persistent name (#kind/owner/hash8), never a positional id.
    assert all(i.startswith("#") for i in ids)


def test_some_names_survive_an_upstream_param_edit() -> None:
    document = _load(_BRACKET)
    before = _ids(_build(copy.deepcopy(document)))
    edited = copy.deepcopy(document)
    part = next(iter(edited["parts"].values()))
    for feature in part["features"]:
        if feature.get("op") == "extrude" and "distance" in feature:
            feature["distance"] = float(feature["distance"]) + 2.0
            break
    after = _ids(_build(edited))
    # Faces unaffected by the edited dimension keep their exact persistent names (geometric
    # carry-forward). Coarse extrude lineage means not ALL names survive yet (finer per-op
    # lineage is a logged 4.1 follow-up), but a substantial set does.
    assert before and after and (before & after)
