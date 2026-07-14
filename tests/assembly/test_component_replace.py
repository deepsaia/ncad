def test_replace_swaps_file_part_keeps_id_placement():
    from ncad.assembly.component_replace import ComponentReplace
    inst = {"id": "bolt", "file": "m6.hocon", "part": "bolt",
            "placement": {"position": [1.0, 2.0, 3.0]},
            "replace": {"file": "m8.hocon", "part": "bolt"}}
    out = ComponentReplace().apply(inst, inst["replace"])
    assert out["id"] == "bolt" and out["file"] == "m8.hocon" and out["part"] == "bolt"
    assert out["placement"] == {"position": [1.0, 2.0, 3.0]}
    assert "replace" not in out


def test_replace_with_assembly_drops_file_part():
    from ncad.assembly.component_replace import ComponentReplace
    inst = {"id": "sub", "file": "a.hocon", "part": "p",
            "replace": {"assembly": "child.asm.hocon"}}
    out = ComponentReplace().apply(inst, inst["replace"])
    assert out["assembly"] == "child.asm.hocon"
    assert "file" not in out and "part" not in out
