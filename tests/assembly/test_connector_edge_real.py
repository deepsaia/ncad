import json
import os
import tempfile

import pytest

pytestmark = pytest.mark.slow


def test_edge_connector_resolves_on_a_real_part():
    from ncad.assembly.connector_resolver import ConnectorResolver
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {"schema_version": 2, "units": "mm", "parts": {"p": {"profile": "solid",
        "connectors": [{"id": "topEdge",
                        "at": "select edges where type='line' and min_z>9.9"}],
        "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 20, "h": 20}]},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10}]}}}
    workdir = tempfile.mkdtemp()
    path = os.path.join(workdir, "p.hocon")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(doc, handle)  # JSON is a valid HOCON subset the SpecLoader accepts

    builder = DocumentBuilder(Build123dKernel())
    resolved = builder.resolve_part_elements(path)
    part_dict, elements = resolved["p"]
    frames, issues = ConnectorResolver().resolve(part_dict["connectors"], elements)
    assert not issues, issues
    assert "topEdge" in frames
