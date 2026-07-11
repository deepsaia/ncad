import pytest

from ncad.build.mass_calculator import MassCalculator
from ncad.build.material_error import MaterialError
from ncad.build.material_resolver import MaterialResolver
from ncad.spec.material_library import MaterialLibrary
from tests.kernel.fake_kernel import FakeKernel


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def _resolver(part):
    return MaterialResolver(part, MaterialLibrary({}))


def test_single_body_mass_is_density_times_volume_converted():
    k = FakeKernel()
    shape = _box(k)  # 1000 mm^3, created_by="" (single implicit body)
    part = {"material": "steel_1018", "features": []}
    props = MassCalculator(k).mass_properties(shape, _resolver(part))
    body = props["bodies"][0]
    assert body["volume"] == pytest.approx(1000.0)
    assert body["density"] == 7870
    # mass_kg = 7870 * 1000 * 1e-9
    assert body["mass"] == pytest.approx(7870 * 1000 * 1e-9)
    assert props["total"]["mass"] == pytest.approx(7870 * 1000 * 1e-9)


def test_two_material_multibody_totals_and_weighted_cog():
    k = FakeKernel()
    a = _box(k, 10, 10, 10)    # 1000
    b = _box(k, 20, 20, 20)    # 8000
    shape = k.union_bodies([a, b], origin="grp")  # grp/body/0, grp/body/1 both created_by grp
    part = {"material": "aluminium_6061", "features": [{"id": "grp", "op": "boolean"}]}
    props = MassCalculator(k).mass_properties(shape, _resolver(part))
    masses = [bd["mass"] for bd in props["bodies"]]
    assert props["total"]["volume"] == pytest.approx(9000.0)
    assert props["total"]["mass"] == pytest.approx(sum(masses))
    assert props["total"]["mass"] == pytest.approx(2700 * 9000 * 1e-9)


def test_missing_material_raises():
    k = FakeKernel()
    shape = _box(k)
    part = {"features": []}  # no part material, single body created_by "" -> None
    with pytest.raises(MaterialError):
        MassCalculator(k).mass_properties(shape, _resolver(part))
