def test_compose_namespaces_ids_and_composes_translation():
    from ncad.assembly.sub_assembly_composer import SubAssemblyComposer
    child = [{"id": "wheel",
              "placement": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [5, 0, 0, 1]],
              "part_glb": "wheel.glb", "part_name": "wheel", "connectors": []}]
    parent = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [10, 0, 0, 1]]
    out = SubAssemblyComposer().compose(child, parent, "caster")
    assert out[0]["id"] == "caster/wheel"
    # child at x=5 under a parent at x=10 -> world x=15.
    assert out[0]["placement"][3][0] == 15.0
    # non-placement fields carry through unchanged.
    assert out[0]["part_glb"] == "wheel.glb"


def test_compose_preserves_multiple_children():
    from ncad.assembly.sub_assembly_composer import SubAssemblyComposer
    child = [
        {"id": "a", "placement": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]},
        {"id": "b", "placement": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [2, 0, 0, 1]]},
    ]
    parent = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 3, 1]]
    out = SubAssemblyComposer().compose(child, parent, "sub")
    assert [i["id"] for i in out] == ["sub/a", "sub/b"]
    assert out[1]["placement"][3][0] == 2.0 and out[1]["placement"][3][2] == 3.0
