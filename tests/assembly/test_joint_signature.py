from ncad.assembly.joint_signature import SIGNATURES, FreeAxis


def test_free_axis_to_dict() -> None:
    assert FreeAxis(motion="rotation", axis="Z").to_dict() == {"motion": "rotation", "axis": "Z"}


def test_signatures_cover_all_seven_joint_types() -> None:
    for jtype in ("fixed", "revolute", "slider", "cylindrical", "planar", "ball", "point_on_line"):
        assert jtype in SIGNATURES


def test_signature_dof_counts() -> None:
    counts = {t: len(SIGNATURES[t]) for t in SIGNATURES}
    assert counts["fixed"] == 0
    assert counts["revolute"] == 1
    assert counts["slider"] == 1
    assert counts["cylindrical"] == 2
    assert counts["planar"] == 3
    assert counts["ball"] == 3
    assert counts["point_on_line"] == 1


def test_revolute_signature_is_rotation_about_z() -> None:
    sig = SIGNATURES["revolute"]
    assert sig == [FreeAxis(motion="rotation", axis="Z")]


def test_slot_alias_matches_point_on_line() -> None:
    assert SIGNATURES["slot"] == SIGNATURES["point_on_line"]
