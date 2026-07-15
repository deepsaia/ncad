from ncad.assembly.coupling import Coupling


def test_coupling_to_dict() -> None:
    c = Coupling(id="c1", type="gear", between=["j1", "j2"], ratio=2.0)
    assert c.to_dict() == {"id": "c1", "type": "gear", "between": ["j1", "j2"], "ratio": 2.0,
                           "profile": None}


def test_coupling_ratio_optional() -> None:
    c = Coupling(id="c1", type="universal", between=["j1", "j2"])
    assert c.ratio is None
    assert c.to_dict()["ratio"] is None


def test_cam_coupling_carries_profile() -> None:
    c = Coupling(id="camPair", type="cam", between=["camJoint", "followerJoint"],
                 profile="select edges where type='bspline'")
    d = c.to_dict()
    assert d["type"] == "cam"
    assert d["profile"] == "select edges where type='bspline'"
