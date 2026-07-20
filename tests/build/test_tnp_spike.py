import pytest

from ncad.build.document_builder import DocumentBuilder
from ncad.build.equality_comparator import EqualityComparator
from tests.kernel.fake_kernel import FakeKernel


def _bracket(thickness=10):
    return {"units": "mm", "parameters": {"t": thickness},
            "parts": {"p": {"profile": "solid", "features": [
                {"id": "sk", "op": "sketch", "plane": "XY",
                 "elements": [{"id": "r", "type": "rectangle", "w": 40, "h": 40}]},
                {"id": "pad", "op": "extrude", "profile": "sk", "distance": "${t}"},
                {"id": "holes", "op": "hole", "on": "pad.cap(+Z)", "diameter": 5,
                 "depth": 4, "positions": [[10, 10]]},
                {"id": "rnd", "op": "fillet", "radius": 3,
                 "edges": "select edges where created_by='pad' and orientation='vertical'"}]}}}


def _without(doc, feature_id):
    doc["parts"]["p"]["features"] = [
        f for f in doc["parts"]["p"]["features"] if f["id"] != feature_id]
    return doc


def test_selector_and_generative_refs_survive_a_param_edit():
    builder = DocumentBuilder(FakeKernel())
    builder.build(_bracket(thickness=10))
    result = builder.build(_bracket(thickness=20))["p"]

    assert result.issues == [] and result.shape is not None
    stats = builder.rebuild_stats()["p"]
    assert stats["sk"] is True
    assert stats["pad"] is False and stats["rnd"] is False


def test_incremental_edit_equals_cold_build():
    warm = DocumentBuilder(FakeKernel())
    warm.build(_bracket(thickness=10))
    warm_shape = warm.build(_bracket(thickness=20))["p"].shape
    cold_shape = DocumentBuilder(FakeKernel()).build(_bracket(thickness=20))["p"].shape

    comparator = EqualityComparator()
    assert comparator.equal(FakeKernel().signature(warm_shape),
                            FakeKernel().signature(cold_shape))


def test_deleting_extrude_fails_loudly_by_id():
    result = DocumentBuilder(FakeKernel()).build(_without(_bracket(), "pad"))["p"]

    assert result.issues, "deleting the extrude must produce id-tagged issues"
    assert all(i.node_id in {"holes", "rnd"} for i in result.issues)


@pytest.mark.slow
def test_bracket_spike_on_real_kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel

    builder = DocumentBuilder(Build123dKernel())
    before = builder.build(_bracket(thickness=10))["p"]
    after = builder.build(_bracket(thickness=20))["p"]

    assert before.issues == [] and after.issues == []
    sig_before = Build123dKernel().signature(before.shape)
    sig_after = Build123dKernel().signature(after.shape)
    assert sig_before["counts"] == sig_after["counts"]
    assert sig_before["surface_types"] == sig_after["surface_types"]

    broken = DocumentBuilder(Build123dKernel()).build(_without(_bracket(), "pad"))["p"]
    assert broken.issues and all(i.node_id in {"holes", "rnd"} for i in broken.issues)
