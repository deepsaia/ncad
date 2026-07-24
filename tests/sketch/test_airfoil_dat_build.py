"""The .dat airfoil resolves through the full build path: DocumentBuilder threads base_dir so
sketch_op -> EntityExpander -> AirfoilProfile can find the file relative to the document."""

import json
import os
import shutil

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "naca0012.dat")


def test_dat_airfoil_resolves_relative_to_the_document(tmp_path):
    # Place the .dat next to a part doc, reference it relatively, and build the doc from that path.
    shutil.copy(_FIXTURE, tmp_path / "naca0012.dat")
    doc = {"units": "mm", "parts": {"blade": {"profile": "solid", "features": [
        {"id": "sk", "op": "sketch", "plane": "XY",
         "entities": [{"id": "a", "type": "airfoil", "dat": "naca0012.dat", "chord": 200}]},
        {"id": "ext", "op": "extrude", "profile": "sk", "distance": 40}]}}}
    doc_path = tmp_path / "blade.json"
    doc_path.write_text(json.dumps(doc))

    builder = DocumentBuilder(Build123dKernel())
    builds = builder.resolve_part_builds(str(doc_path))

    assert builds["blade"][0] is not None   # the .dat airfoil built a real solid
