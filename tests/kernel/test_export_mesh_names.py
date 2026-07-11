import json
import struct
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _glb_mesh_count(path: str) -> int:
    """Parse a .glb and return its glTF mesh count."""
    with open(path, "rb") as handle:
        handle.read(12)  # magic, version, length
        chunk_len, _chunk_type = struct.unpack("<II", handle.read(8))
        gltf = json.loads(handle.read(chunk_len))
    return len(gltf.get("meshes", []))


def test_multibody_export_meshes_align_with_body_order(tmp_path):
    # The sidecar `meshes` list (body id per exported glTF mesh, in export order) must parallel
    # the exported glb's meshes, so the viewer maps mesh index -> body -> material positionally.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    doc = _EXAMPLES / "gate-3.6" / "flanged_coupling.hocon"
    artifacts = builder.build_file(str(doc), str(tmp_path), formats=("glb",))
    mesh_count = _glb_mesh_count(artifacts["flanged_coupling"])

    sidecar = json.loads((tmp_path / "flanged_coupling.elementmap.json").read_text())
    meshes = sidecar["meshes"]
    # one sidecar mesh entry per exported glTF mesh
    assert len(meshes) == mesh_count
    # each carries a body id + its material; the coupling has aluminium flanges + steel hubs
    body_ids = {m["body_id"] for m in meshes}
    materials = {m["material"] for m in meshes}
    assert len(body_ids) == 4  # 2 flanges + 2 hubs
    assert materials == {"aluminium_6061", "steel_1018"}
