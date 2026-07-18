from ncad.assembly.asmt_exporter import AsmtExporter

# A minimal single-instance model is enough to inspect the emitted motions (the exporter needs
# pyondsel importable; it is installed editable). Identity placement, one connector marker.
_PLACEMENT = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
              [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _model(secondaries):
    from ncad.assembly.connector_frame import ConnectorFrame

    instances = [{"id": "a"}]
    local_frames = {"a": {"hub": ConnectorFrame.from_axis((0.0, 0.0, 0.0), (0.0, 0.0, 1.0),
                                                          None, None)}}
    placements_mm = {"a": _PLACEMENT}
    mass_props = {"a": {"mass": 1.0, "cog": (0, 0, 0), "inertia": {"principal": [1, 1, 1]}}}
    joints: list[dict] = []
    driver = {"joint_id": "mainPin", "joint_type": "revolute", "pivot": None, "moving": None,
              "values": [0.0, 90.0, 180.0], "start": 0.0, "end": 180.0}
    return AsmtExporter().build_model("m", instances, local_frames, placements_mm, mass_props,
                                      joints, set(), driver, 0.001, secondaries=secondaries)


def test_primary_plus_one_secondary_motion():
    model = _model([{"joint_id": "gearPin", "joint_type": "revolute", "expression": "-0.5 * time"}])
    names = {mo.name for mo in model.motions}
    assert "drive_mainPin" in names          # the primary
    assert "couple_gearPin" in names         # the secondary
    gear = next(mo for mo in model.motions if mo.name == "couple_gearPin")
    assert gear.joint == "gearPin" and gear.kind == "rotational"
    assert gear.expression == "-0.5 * time"


def test_slider_secondary_is_translational():
    model = _model([{"joint_id": "rack", "joint_type": "slider", "expression": "0.015 * time"}])
    rack = next(mo for mo in model.motions if mo.name == "couple_rack")
    assert rack.kind == "translational"


def test_no_secondaries_leaves_only_the_primary():
    model = _model([])
    assert [mo.name for mo in model.motions] == ["drive_mainPin"]


def test_non_drivable_secondary_is_skipped():
    model = _model([{"joint_id": "ball", "joint_type": "ball", "expression": "time"}])
    names = {mo.name for mo in model.motions}
    assert "couple_ball" not in names and "drive_mainPin" in names
