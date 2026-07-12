from ncad.assembly.coupling import Coupling


def test_coupling_to_dict() -> None:
    c = Coupling(id="c1", type="gear", between=["j1", "j2"], ratio=2.0)
    assert c.to_dict() == {"id": "c1", "type": "gear", "between": ["j1", "j2"], "ratio": 2.0}


def test_coupling_ratio_optional() -> None:
    c = Coupling(id="c1", type="universal", between=["j1", "j2"])
    assert c.ratio is None
    assert c.to_dict()["ratio"] is None
