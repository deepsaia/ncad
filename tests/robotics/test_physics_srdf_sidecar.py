"""ncad physics writes a .srdf sidecar beside the urdf (default-group path on the desk_arm)."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from ncad.cli.viewer_cli import ViewerCli


@pytest.mark.slow
def test_physics_export_writes_srdf_sidecar(tmp_path):
    result = ViewerCli().physics_document(
        "examples/08-robotics/desk_arm.physics.hocon", str(tmp_path))
    srdf = result.get("srdf")
    assert srdf and Path(srdf).is_file()

    urdf_links = {link.attrib["name"]
                  for link in ET.fromstring(Path(result["artifact"]).read_text()).findall("link")}
    root = ET.fromstring(Path(srdf).read_text())
    assert root.tag == "robot"
    # Every chain base/tip link named in the SRDF exists in the paired URDF.
    for chain in root.iter("chain"):
        assert chain.attrib["base_link"] in urdf_links
        assert chain.attrib["tip_link"] in urdf_links
    # Adjacency pairs reference only real links too.
    for disable in root.findall("disable_collisions"):
        assert disable.attrib["link1"] in urdf_links
        assert disable.attrib["link2"] in urdf_links


@pytest.mark.slow
def test_no_srdf_flag_suppresses_the_sidecar(tmp_path):
    result = ViewerCli().physics_document(
        "examples/08-robotics/desk_arm.physics.hocon", str(tmp_path), write_srdf=False)
    assert result.get("srdf") is None
