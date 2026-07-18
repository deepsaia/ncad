import pytest

from ncad.build.material_error import MaterialError
from ncad.spec.material_library import MaterialLibrary


def test_seed_resolves_steel_density():
    lib = MaterialLibrary({})
    assert lib.resolve("steel_1018")["physical"]["density"] == 7870
    assert lib.has("aluminium_6061") and lib.has("abs")


def test_seed_bronze_has_appearance_color():
    # Bronze carries a warm appearance color so it reads distinctly in the viewer + glTF/STEP.
    lib = MaterialLibrary({})
    bronze = lib.resolve("bronze")
    assert bronze["physical"]["density"] == 8800
    assert bronze["appearance"]["color"] == [0.72, 0.45, 0.20]


def test_unknown_material_raises():
    lib = MaterialLibrary({})
    with pytest.raises(MaterialError, match="titanium"):
        lib.resolve("titanium")


def test_inline_materials_add_and_override_seed():
    doc = {"materials": {
        "brass": {"physical": {"density": 8500}},
        "steel_1018": {"physical": {"density": 7900}},  # override seed density
    }}
    lib = MaterialLibrary(doc)
    assert lib.resolve("brass")["physical"]["density"] == 8500
    assert lib.resolve("steel_1018")["physical"]["density"] == 7900  # inline beats seed


def test_inline_override_deep_merges_onto_referenced():
    doc = {"materials": {"steel_hot": {"physical": {"density": 7700}}}}
    lib = MaterialLibrary(doc)
    # override only the density; the referenced record's other groups survive
    merged = lib.resolve("steel_1018", override={"physical": {"density": 7000}})
    assert merged["physical"]["density"] == 7000
    assert merged["structural"]["poisson"] == 0.29  # untouched from seed


def test_external_library_file_is_loaded_and_merged(tmp_path):
    ext = tmp_path / "extra.hocon"
    ext.write_text("titanium { physical { density = 4506 } }\n")
    doc = {"materials_library": "extra.hocon"}
    lib = MaterialLibrary(doc, base_dir=str(tmp_path))
    assert lib.resolve("titanium")["physical"]["density"] == 4506
    assert lib.resolve("steel_1018")["physical"]["density"] == 7870  # seed still present


def test_inline_beats_external(tmp_path):
    ext = tmp_path / "extra.hocon"
    ext.write_text("brass { physical { density = 8000 } }\n")
    doc = {"materials_library": "extra.hocon",
           "materials": {"brass": {"physical": {"density": 8500}}}}
    lib = MaterialLibrary(doc, base_dir=str(tmp_path))
    assert lib.resolve("brass")["physical"]["density"] == 8500  # inline > external


def test_malformed_record_raises():
    with pytest.raises(MaterialError, match="invalid"):
        MaterialLibrary({"materials": {"bad": {"physical": {"density": -5}}}})
