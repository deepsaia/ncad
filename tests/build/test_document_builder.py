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
