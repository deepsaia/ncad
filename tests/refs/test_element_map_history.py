from ncad.kernel.element_history import ElementHistory
from ncad.refs.element_map import ElementMap


def _face(handle: str, center: tuple, area: float) -> dict:
    return {"kind": "face", "handle": handle, "geom_type": "planar",
            "normal": (0.0, 0.0, 1.0), "area": area, "center": center}


def test_rebuild_with_history_assigns_persistent_names() -> None:
    em = ElementMap()
    descriptors = [_face("h1", (0.0, 0.0, 0.0), 10.0)]
    hist = ElementHistory(generated_from={"h1": []})
    em.rebuild("pad", descriptors, {}, hist)
    ids = [e.id for e in em.elements()]
    assert ids[0].startswith("#face/pad/")


def test_carried_name_survives_a_second_rebuild() -> None:
    em = ElementMap()
    d1 = [_face("h1", (0.0, 0.0, 0.0), 10.0)]
    em.rebuild("pad", d1, {}, ElementHistory(generated_from={"h1": []}))
    first = em.elements()[0].id
    # A later op carries the same handle unchanged: its name must persist.
    d2 = [_face("h1", (0.0, 0.0, 0.0), 10.0)]
    em.rebuild("fillet", d2, {}, ElementHistory())
    assert em.elements()[0].id == first


def test_rebuild_without_history_still_works() -> None:
    em = ElementMap()
    descriptors = [_face("h1", (0.0, 0.0, 0.0), 10.0)]
    em.rebuild("legacy", descriptors, {})  # no history arg
    assert em.elements()[0].id.startswith("#face/legacy/")
