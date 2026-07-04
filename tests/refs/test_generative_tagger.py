from ncad.refs.generative_tagger import GenerativeTagger


def _face(nx, ny, nz, cz, area=100.0):
    return {"kind": "face", "normal": (nx, ny, nz), "area": area,
            "center": (0.0, 0.0, cz), "min_z": cz, "mid_z": cz, "max_z": cz}


def test_extrude_xy_tags_caps_and_sides():
    faces = [
        _face(0, 0, 1, 5),    # top cap
        _face(0, 0, -1, 0),   # bottom cap
        _face(1, 0, 0, 2.5),  # side
        _face(-1, 0, 0, 2.5), # side
    ]
    tags = GenerativeTagger().tags_for("extrude", "XY", faces)
    assert tags[0] == "cap(+Z)"
    assert tags[1] == "cap(-Z)"
    assert tags[2] == "side" and tags[3] == "side"


def test_non_extrude_op_has_no_tags():
    faces = [_face(0, 0, 1, 5)]
    assert GenerativeTagger().tags_for("hole", "XY", faces) == {}
