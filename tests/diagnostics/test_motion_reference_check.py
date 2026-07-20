from ncad.diagnostics import codes
from ncad.diagnostics.checks.motion_reference_check import MotionReferenceCheck

_ASM = {"joints": [{"id": "pin", "type": "revolute"}, {"id": "sl", "type": "slider"},
                   {"id": "fx", "type": "fixed"}],
        "couplings": [{"id": "c", "type": "gear", "between": ["pin", "sl"]}]}


def _motion(driver):
    return {"motion": {"assembly": "a.asm.hocon", "driver": driver}}


def test_valid_motion_yields_nothing():
    assert MotionReferenceCheck().check(_motion({"joint": "pin"}), _ASM) == []


def test_driver_joint_missing():
    diags = MotionReferenceCheck().check(_motion({"joint": "ghost"}), _ASM)
    assert [d.code for d in diags] == [codes.DRIVER_JOINT_MISSING]


def test_driver_joint_not_drivable():
    diags = MotionReferenceCheck().check(_motion({"joint": "fx"}), _ASM)
    assert [d.code for d in diags] == [codes.DRIVER_JOINT_NOT_DRIVABLE]


def test_assembly_unresolvable():
    diags = MotionReferenceCheck().check(_motion({"joint": "pin"}), None)
    assert diags[0].code == codes.MOTION_ASSEMBLY_MISSING


def test_coupling_primary_mismatch_is_warning():
    asm = {"joints": _ASM["joints"],
           "couplings": [{"id": "c", "type": "gear", "between": ["sl", "pin"]}]}
    diags = MotionReferenceCheck().check(_motion({"joint": "pin"}), asm)
    assert [(d.code, d.severity) for d in diags] == [(codes.COUPLING_PRIMARY_MISMATCH, "warning")]
