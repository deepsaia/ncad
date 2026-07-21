"""Unit tests for AssemblyBuilder._expected_contact_pairs (bucket: interference pruning).

The method is pure (no kernel use): it derives the instance-id pairs that mesh by design, which the
static interference check reports as expected_contact and skips measuring. A gear coupling whose two
joints share one frame is auto-detected; a belt coupling is not (a belt spans a gap, no contact);
the explicit expected_contact block always applies.
"""

import pytest

pytestmark = pytest.mark.slow  # AssemblyBuilder.__init__ imports the kernel stack


def _builder():
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    return AssemblyBuilder(Build123dKernel())


def test_gear_coupling_with_shared_frame_auto_detects_the_two_wheels() -> None:
    # A gear_pair: pinion + gear turn on ONE stand; the mesh pair is pinion<>gear (stand dropped).
    document = {"assembly": {"joints": [
        {"id": "pinionPin", "between": [{"instance": "stand"}, {"instance": "pinion"}]},
        {"id": "gearPin", "between": [{"instance": "stand"}, {"instance": "gear"}]}],
        "couplings": [
            {"id": "mesh", "type": "gear", "between": ["pinionPin", "gearPin"]}]}}
    pairs = _builder()._expected_contact_pairs(document)
    assert pairs == {frozenset(("pinion", "gear"))}


def test_belt_coupling_declares_no_contact() -> None:
    # A belt ties two pulleys that do NOT touch (the belt spans the gap): no expected-contact pair.
    document = {"assembly": {"joints": [
        {"id": "aPin", "between": [{"instance": "frame"}, {"instance": "pulleyA"}]},
        {"id": "bPin", "between": [{"instance": "frame"}, {"instance": "pulleyB"}]}],
        "couplings": [
            {"id": "belt", "type": "belt", "between": ["aPin", "bPin"]}]}}
    assert _builder()._expected_contact_pairs(document) == set()


def test_gear_coupling_across_a_moving_carrier_is_not_auto_detected() -> None:
    # sun on the ground, planet on a moving carrier: the two joints share NO instance, so the mesh
    # pair is ambiguous and NOT auto-detected (the author declares it via expected_contact instead).
    document = {"assembly": {"joints": [
        {"id": "sunPin", "between": [{"instance": "stand"}, {"instance": "sun"}]},
        {"id": "planetPin", "between": [{"instance": "carrier"}, {"instance": "planet"}]}],
        "couplings": [
            {"id": "mesh", "type": "gear", "between": ["sunPin", "planetPin"]}]}}
    assert _builder()._expected_contact_pairs(document) == set()


def test_explicit_expected_contact_block_is_honoured() -> None:
    document = {"assembly": {"expected_contact": [["ring", "planet0"], ["sun", "planet0"]]}}
    pairs = _builder()._expected_contact_pairs(document)
    assert pairs == {frozenset(("ring", "planet0")), frozenset(("sun", "planet0"))}


def test_a_plain_joint_alone_declares_no_contact() -> None:
    # A revolute/slider joint is NOT expected-contact: pivoting bodies must not interpenetrate, so a
    # clash there is a real finding (the clearance_probe gate).
    document = {"assembly": {"joints": [
        {"id": "armPin", "between": [{"instance": "base"}, {"instance": "arm"}]}]}}
    assert _builder()._expected_contact_pairs(document) == set()
