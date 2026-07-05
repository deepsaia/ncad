from ncad.sketch.id_padding import PaddedNaming


def test_small_count_width_one():
    assert PaddedNaming().child_ids("h", 3) == ["h/0", "h/1", "h/2"]


def test_ten_is_width_one():
    ids = PaddedNaming().child_ids("h", 10)
    assert ids[0] == "h/0" and ids[9] == "h/9"


def test_eleven_is_width_two():
    ids = PaddedNaming().child_ids("h", 11)
    assert ids[0] == "h/00" and ids[10] == "h/10"


def test_hundred_and_one_is_width_three():
    ids = PaddedNaming().child_ids("h", 101)
    assert ids[0] == "h/000" and ids[100] == "h/100"


def test_lexical_sort_matches_numeric():
    ids = PaddedNaming().child_ids("h", 12)
    assert sorted(ids) == ids


def test_zero_count_is_empty():
    assert PaddedNaming().child_ids("h", 0) == []
