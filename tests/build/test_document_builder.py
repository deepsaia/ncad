from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder
from tests.kernel.fake_kernel import FakeKernel

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "gate-0.1-first-shape"
    / "block.hocon"
)


def _document() -> dict:
    return {
        "schema_version": 2,
        "units": "mm",
        "parts": {
            "block": {
                "profile": "solid",
                "features": [
                    {
                        "id": "sk",
                        "op": "sketch",
                        "plane": "XY",
                        "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
                    },
                    {"id": "pad", "op": "extrude", "profile": "sk", "distance": 8.0},
                ],
            }
        },
    }


def test_build_returns_result_per_part() -> None:
    builder = DocumentBuilder(FakeKernel())

    results = builder.build(_document())

    assert set(results) == {"block"}
    assert results["block"].issues == []
    assert FakeKernel().volume(results["block"].shape) == 80.0 * 60.0 * 8.0


def test_build_rejects_schema_invalid_document() -> None:
    builder = DocumentBuilder(FakeKernel())
    bad = _document()
    del bad["units"]

    with pytest.raises(ValueError, match="schema"):
        builder.build(bad)


def test_fixture_document_is_loadable_and_builds() -> None:
    builder = DocumentBuilder(FakeKernel())

    results = builder.build_file_document(str(_FIXTURE))

    assert results["block"].issues == []


@pytest.mark.slow
def test_build_file_exports_glb(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    builder = DocumentBuilder(Build123dKernel())

    artifacts = builder.build_file(str(_FIXTURE), str(tmp_path))

    glb = Path(artifacts["block"])
    assert glb.is_file() and glb.stat().st_size > 0
    assert glb.name == "block.glb"


@pytest.mark.slow
def test_build_file_writes_hierarchy_sidecar(tmp_path) -> None:
    import json

    from ncad.kernel.build123d_kernel import Build123dKernel

    DocumentBuilder(Build123dKernel()).build_file(str(_FIXTURE), str(tmp_path))

    sidecar = tmp_path / "block.hierarchy.json"
    assert sidecar.is_file()
    data = json.loads(sidecar.read_text())
    assert data["name"] == "block" and data["kind"] == "part"
    assert [c["id"] for c in data["children"]] == ["sk", "pad"]


def test_build_resolves_parameters_and_expressions() -> None:
    builder = DocumentBuilder(FakeKernel())
    doc = {
        "schema_version": 2, "units": "mm",
        "parameters": {"w": 80, "h": 60, "t": 8},
        "parts": {"block": {"profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": "${w}", "h": "${h}"}]},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": "${t}"},
        ]}},
    }

    results = builder.build(doc)

    assert results["block"].issues == []
    assert FakeKernel().volume(results["block"].shape) == 80.0 * 60.0 * 8.0


def test_build_file_writes_elementmap_sidecar(tmp_path) -> None:
    import json

    doc = {"schema_version": 1, "units": "mm", "parts": {"blk": {
        "profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 20, "h": 20}]},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 5}]}}}
    builder = DocumentBuilder(FakeKernel())

    sidecars = builder.write_element_maps(doc, str(tmp_path))

    path = sidecars["blk"]
    data = json.loads(Path(path).read_text())
    assert data["elements"] and "attribute_model_version" in data
    assert any(e["tag"] == "cap(+Z)" for e in data["elements"])


def test_build_raises_on_expression_error() -> None:
    from ncad.params.expression_error import ExpressionError

    builder = DocumentBuilder(FakeKernel())
    bad = {
        "schema_version": 2, "units": "mm",
        "parameters": {"x": "${missing} + 1"},
        "parts": {"block": {"profile": "solid", "features": []}},
    }

    with pytest.raises(ExpressionError):
        builder.build(bad)


def test_incremental_rebuild_reuses_unchanged_features() -> None:
    from ncad.build.equality_comparator import EqualityComparator
    from tests.kernel.fake_kernel import FakeKernel

    kernel = FakeKernel()
    builder = DocumentBuilder(kernel)

    def doc(thickness):
        return {"schema_version": 1, "units": "mm", "parameters": {"t": thickness},
                "parts": {"blk": {"profile": "solid", "features": [
                    {"id": "sk", "op": "sketch", "plane": "XY",
                     "elements": [{"id": "r", "type": "rectangle", "w": 40, "h": 40}]},
                    {"id": "pad", "op": "extrude", "profile": "sk", "distance": "${t}"},
                    {"id": "h", "op": "hole", "diameter": 4, "depth": 3,
                     "positions": [[10, 10]]}]}}}

    builder.build(doc(8))
    results = builder.build(doc(10))
    stats = builder.rebuild_stats()

    assert stats["blk"] == {"sk": True, "pad": False, "h": False}
    cold = DocumentBuilder(FakeKernel()).build(doc(10))
    comparator = EqualityComparator()
    assert comparator.equal(kernel.signature(results["blk"].shape),
                            FakeKernel().signature(cold["blk"].shape))


def test_same_document_builds_are_deterministic() -> None:
    from ncad.build.equality_comparator import EqualityComparator
    from tests.kernel.fake_kernel import FakeKernel

    doc = {"schema_version": 1, "units": "mm", "parts": {"blk": {
        "profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 20, "h": 30}]},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 5}]}}}
    a = DocumentBuilder(FakeKernel()).build(doc)["blk"].shape
    b = DocumentBuilder(FakeKernel()).build(doc)["blk"].shape
    assert EqualityComparator().equal(FakeKernel().signature(a), FakeKernel().signature(b))


def test_build_rejects_forward_reference() -> None:
    import pytest

    from tests.kernel.fake_kernel import FakeKernel

    doc = {"schema_version": 1, "units": "mm", "parts": {"p": {
        "profile": "solid", "features": [
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 5},
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 20, "h": 20}]}]}}}

    with pytest.raises(ValueError, match="dependency"):
        DocumentBuilder(FakeKernel()).build(doc)


def testresolve_formats_accepts_known():
    from ncad.build.document_builder import resolve_formats
    assert resolve_formats(("glb",)) == ("glb",)
    assert resolve_formats(("glb", "step")) == ("glb", "step")


def testresolve_formats_rejects_unknown():
    from ncad.build.document_builder import resolve_formats
    with pytest.raises(ValueError, match="glb"):
        resolve_formats(("iges",))
