import pytest

from ncad.ops.extrude_params import ExtrudeParamError, extrude_kwargs


def test_blind_default():
    assert extrude_kwargs({"distance": 8}, {}) == {"distance": 8.0, "draft": 0.0}


def test_symmetric():
    kw = extrude_kwargs({"end": "symmetric", "distance": 20}, {})
    assert kw["symmetric"] is True and kw["distance"] == 20.0


def test_two_side():
    kw = extrude_kwargs({"end": "two_side", "distance": 20, "second_distance": 8}, {})
    assert kw["distance"] == 20.0 and kw["second_distance"] == 8.0


def test_through_all():
    kw = extrude_kwargs({"end": "through_all"}, {})
    assert kw["until"] == "last"


def test_to_next():
    kw = extrude_kwargs({"end": "to_next"}, {})
    assert kw["until"] == "next"


def test_to_face_uses_resolved_target():
    target = object()
    kw = extrude_kwargs({"end": "to_face", "to": "select faces where ..."},
                        {"to": target})
    assert kw["target"] is target


def test_draft_and_thin_modifiers():
    kw = extrude_kwargs({"distance": 10, "draft": 3, "thin": 2}, {})
    assert kw["draft"] == 3.0 and kw["thin"] == 2.0


def test_unknown_end_raises():
    with pytest.raises(ExtrudeParamError, match="end"):
        extrude_kwargs({"end": "warp", "distance": 5}, {})


def test_blind_missing_distance_raises():
    with pytest.raises(ExtrudeParamError, match="distance"):
        extrude_kwargs({"end": "blind"}, {})


def test_two_side_missing_second_distance_raises():
    with pytest.raises(ExtrudeParamError, match="second_distance"):
        extrude_kwargs({"end": "two_side", "distance": 10}, {})


def test_to_face_missing_target_raises():
    with pytest.raises(ExtrudeParamError, match="to"):
        extrude_kwargs({"end": "to_face"}, {})


def test_bare_symmetric_flag_without_end_raises():
    # `symmetric` is selected by end = symmetric, not a bare boolean; a stray flag must fail
    # loudly rather than be silently dropped (which would build a one-sided blind extrude).
    with pytest.raises(ExtrudeParamError, match="symmetric"):
        extrude_kwargs({"distance": 6, "symmetric": True}, {})


def test_bare_second_distance_without_two_side_raises():
    with pytest.raises(ExtrudeParamError, match="second_distance"):
        extrude_kwargs({"distance": 6, "second_distance": 3}, {})


def test_end_symmetric_sets_symmetric_kwarg():
    kw = extrude_kwargs({"end": "symmetric", "distance": 6}, {})
    assert kw["symmetric"] is True and kw["distance"] == 6.0
