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


def test_untagged_op_has_no_tags():
    # An op with no generative-tag rule (e.g. a plain boolean) tags nothing.
    faces = [_face(0, 0, 1, 5)]
    assert GenerativeTagger().tags_for("boolean", "XY", faces) == {}


def _curved_face(geom_type: str) -> dict:
    return {"kind": "face", "geom_type": geom_type, "normal": (1.0, 0.0, 0.0),
            "center": (0.0, 0.0, 0.0), "area": 5.0}


def test_fillet_faces_tagged_fillet():
    faces = [_curved_face("cylinder")]
    tags = GenerativeTagger().tags_for("fillet", "XY", faces)
    assert tags.get(0) == "fillet"


def test_chamfer_faces_tagged_chamfer():
    faces = [_curved_face("cone")]
    tags = GenerativeTagger().tags_for("chamfer", "XY", faces)
    assert tags.get(0) == "chamfer"


def test_hole_walls_tagged():
    faces = [_curved_face("cylinder")]
    tags = GenerativeTagger().tags_for("hole", "XY", faces)
    assert tags.get(0) == "hole_wall"
