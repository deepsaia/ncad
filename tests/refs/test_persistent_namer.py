from ncad.kernel.element_history import ElementHistory
from ncad.refs.persistent_namer import PersistentNamer, geometric_seed_name


def _face(handle: str, center: tuple, area: float, normal: tuple = (0.0, 0.0, 1.0)) -> dict:
    return {"kind": "face", "handle": handle, "geom_type": "plane",
            "normal": normal, "area": area, "center": center}


def test_geometric_seed_name_is_deterministic() -> None:
    d = _face("h1", (1.0, 2.0, 3.0), 10.0)
    a = geometric_seed_name("face", d, "import")
    b = geometric_seed_name("face", d, "import")
    assert a == b
    assert a.startswith("#face/import/")
    assert len(a.rsplit("/", 1)[1]) == 8


def test_generated_element_gets_fresh_hashed_name() -> None:
    namer = PersistentNamer()
    descriptors = [_face("out1", (0.0, 0.0, 5.0), 100.0)]
    hist = ElementHistory(generated_from={"out1": ["in1"]})
    names = namer.name_elements("pad", "extrude", descriptors, {}, hist,
                                prior_by_handle={"in1": "#face/base/aaaaaaaa"})
    assert names[0].startswith("#face/pad/")
    # Deterministic: same inputs, same name.
    again = namer.name_elements("pad", "extrude", descriptors, {}, hist,
                                prior_by_handle={"in1": "#face/base/aaaaaaaa"})
    assert names == again


def test_modified_single_parent_inherits_name() -> None:
    namer = PersistentNamer()
    descriptors = [_face("out2", (0.0, 0.0, 0.0), 50.0)]
    hist = ElementHistory(modified_from={"out2": ["in2"]})
    names = namer.name_elements("cut", "cut", descriptors, {}, hist,
                                prior_by_handle={"in2": "#face/base/bbbbbbbb"})
    assert names[0] == "#face/base/bbbbbbbb"


def test_carried_element_keeps_prior_name() -> None:
    namer = PersistentNamer()
    descriptors = [_face("keep", (2.0, 0.0, 0.0), 20.0)]
    # keep is in neither map but has a prior name: it was carried unchanged.
    names = namer.name_elements("fillet", "fillet", descriptors, {}, ElementHistory(),
                                prior_by_handle={"keep": "#face/base/cccccccc"})
    assert names[0] == "#face/base/cccccccc"


def test_no_history_falls_back_to_geometric_seed() -> None:
    namer = PersistentNamer()
    descriptors = [_face("x", (0.0, 0.0, 0.0), 5.0)]
    names = namer.name_elements("import", "import", descriptors, {}, None, prior_by_handle={})
    assert names[0].startswith("#face/import/")
