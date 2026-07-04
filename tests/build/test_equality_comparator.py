from ncad.build.equality_comparator import EqualityComparator


def _sig(volume=1000.0, faces=6):
    return {
        "counts": {"face": faces, "edge": 12, "vertex": 8},
        "surface_types": {"plane": 6}, "curve_types": {"line": 12},
        "volume": volume, "area": 600.0,
        "bbox": ((0.0, 0.0, 0.0), (10.0, 10.0, 10.0)), "cog": (5.0, 5.0, 5.0),
    }


def test_identical_signatures_are_equal():
    assert EqualityComparator().equal(_sig(), _sig())


def test_topology_count_difference_is_unequal():
    assert not EqualityComparator().equal(_sig(faces=6), _sig(faces=7))


def test_measure_within_tolerance_is_equal():
    assert EqualityComparator().equal(_sig(volume=1000.0), _sig(volume=1000.0 + 1e-7))


def test_measure_past_tolerance_is_unequal():
    assert not EqualityComparator().equal(_sig(volume=1000.0), _sig(volume=1001.0))


def test_explain_names_the_mismatching_field():
    fields = EqualityComparator().explain(_sig(volume=1000.0), _sig(volume=1001.0))
    assert any("volume" in f for f in fields)


def test_explain_empty_when_equal():
    assert EqualityComparator().explain(_sig(), _sig()) == []
