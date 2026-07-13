from ncad.assembly.assembly_bom import AssemblyBom

_ID = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _at(x, y, z):
    return [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [x, y, z, 1]]


def test_groups_by_part_with_quantity_and_mass() -> None:
    instances = [
        {"id": "g1", "file": "p.hocon", "part": "gear"},
        {"id": "g2", "file": "p.hocon", "part": "gear"},
        {"id": "b", "file": "p.hocon", "part": "block"},
    ]
    part_mass = {
        ("p.hocon", "gear"): {"mass": 2.0, "material": "steel", "cog": (0.0, 0.0, 0.0)},
        ("p.hocon", "block"): {"mass": 5.0, "material": "alu", "cog": (0.0, 0.0, 0.0)},
    }
    placements = {"g1": _at(-10, 0, 0), "g2": _at(10, 0, 0), "b": _at(0, 0, 0)}
    out = AssemblyBom().compute(instances, part_mass, placements)
    items = {i["part"]: i for i in out["items"]}
    assert items["gear"]["quantity"] == 2 and items["gear"]["total_mass"] == 4.0
    assert items["block"]["quantity"] == 1
    # Roll-up: 2 gears (2kg each at x=-10/+10) + 1 block (5kg at 0) = 9kg; gears cancel in x, block
    # at 0 -> assembly COG x = 0.
    assert out["mass"]["total_mass"] == 9.0
    assert out["mass"]["cog"][0] == 0.0


def test_no_density_part_counted_but_omitted_from_mass() -> None:
    instances = [{"id": "x", "file": "p.hocon", "part": "widget"}]
    part_mass = {("p.hocon", "widget"): {"mass": None, "material": None, "cog": (0.0, 0.0, 0.0)}}
    out = AssemblyBom().compute(instances, part_mass, {"x": _ID})
    assert out["items"][0]["quantity"] == 1
    assert out["items"][0]["total_mass"] is None
    assert out["mass"]["total_mass"] == 0.0  # nothing with known mass
