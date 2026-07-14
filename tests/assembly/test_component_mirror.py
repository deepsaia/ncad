def test_reflect_across_yz_negates_x():
    from ncad.assembly.component_mirror import ComponentMirror
    src = {"id": "left", "file": "b.hocon", "part": "bracket",
           "placement": {"position": [10.0, 5.0, 0.0]}}
    inst = {"id": "right", "mirror": {"plane": "YZ"}, "of": "left"}
    out = ComponentMirror().reflect(inst, src, "YZ")
    assert out["id"] == "right"
    assert out["file"] == "b.hocon" and out["part"] == "bracket"
    assert out["placement"]["position"][0] == -10.0
    assert out["placement"]["position"][1] == 5.0
    assert "mirror" not in out and "of" not in out


def test_reflect_across_custom_plane_normal():
    from ncad.assembly.component_mirror import ComponentMirror
    src = {"id": "a", "file": "b.hocon", "part": "p", "placement": {"position": [0.0, 4.0, 0.0]}}
    inst = {"id": "b", "of": "a"}
    out = ComponentMirror().reflect(inst, src, {"normal": [0.0, 1.0, 0.0]})
    assert out["placement"]["position"][1] == -4.0
