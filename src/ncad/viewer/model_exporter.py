"""Re-export a document to a chosen format and return the downloadable bytes (no out/ write).

The viewer's export control hands this a recorded SOURCE spec + a target format; it re-runs ncad's
export into a throwaway temp dir and returns ``(download_name, content_type, bytes)`` for the server
to stream to the browser. Re-exporting from the source (not converting the loaded GLB) keeps every
format faithful: a STEP/IGES B-rep and a URDF robot cannot be reconstructed from a display mesh.

Dispatch by format family:

- part mesh/B-rep (glb/step/iges/stl/3mf/obj/ply) -> DocumentBuilder.build_file, one artifact;
- assembly (step) -> AssemblyBuilder writes the AP242 assembly STEP;
- robot (urdf/mjcf/sdf) -> RobotModelBuilder + the format writer, plus per-link meshes -> zipped.

Nothing is written to the models dir; the temp dir is discarded after the bytes are read. One class.
"""

import io
import zipfile
from pathlib import Path
from typing import Any

# format -> MIME type for the download response; unknown falls back to octet-stream.
_CONTENT_TYPES = {
    "glb": "model/gltf-binary", "step": "application/step", "iges": "application/iges",
    "stl": "model/stl", "3mf": "model/3mf", "obj": "text/plain", "ply": "application/octet-stream",
    "urdf": "application/xml", "mjcf": "application/xml", "sdf": "application/xml",
    "zip": "application/zip",
}
# The part formats DocumentBuilder.build_file can emit (extension == format key here).
_PART_FORMATS = frozenset({"glb", "step", "iges", "stl", "3mf", "obj", "ply"})
_ROBOT_FORMATS = frozenset({"urdf", "mjcf", "sdf"})


class ModelExporter:
    """Re-exports a source spec to a format, returning the download bytes (temp dir, no out/)."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel

    def export(self, source: str, kind: str, fmt: str, base_name: str,
               part: str | None = None) -> tuple[str, str, bytes]:
        """Return ``(download_name, content_type, data)`` for ``source`` exported to ``fmt``.

        ``kind`` is the document kind (part/assembly/motion/physics); ``base_name`` is the stem used
        for the downloaded file. ``part`` names WHICH part of a multi-part source document to export
        (e.g. an assembly member ``block`` of ``crank_slider.hocon``); None exports the source's
        single part. Raises ValueError for a format the kind cannot produce.
        """
        import tempfile

        with tempfile.TemporaryDirectory(prefix="ncad-export-") as tmp:
            if kind == "physics" and fmt in _ROBOT_FORMATS:
                return self._export_robot(source, fmt, base_name, Path(tmp))
            if kind == "motion" and fmt == "step":
                # A motion document is not an assembly document (it carries a `motion` block, not
                # `units`+`assembly`); resolve the assembly it drives and export THAT, exactly as
                # MotionBuilder locates the mechanism before solving.
                return self._export_assembly_step(
                    self._motion_assembly_path(source), base_name, Path(tmp))
            if kind == "assembly" and fmt == "step":
                return self._export_assembly_step(source, base_name, Path(tmp))
            if kind == "part" and fmt in _PART_FORMATS:
                return self._export_part(source, fmt, base_name, Path(tmp), part)
            raise ValueError(f"{kind} cannot be exported to {fmt!r}")

    def _export_part(self, source: str, fmt: str, base_name: str,
                     tmp: Path, part: str | None) -> tuple[str, str, bytes]:
        """Build the part source to a single ``fmt`` artifact and return its bytes.

        ``part`` picks WHICH part of a multi-part document to export (an assembly member, or one of
        several parts declared in one .hocon); None means the document declares a single part and
        that one is returned. Raises ValueError if the named part is not in the built artifacts.
        """
        from ncad.build.document_builder import DocumentBuilder

        artifacts = DocumentBuilder(self._kernel).build_file(
            source, str(tmp), formats=(fmt,))["artifacts"]
        if part is not None:
            if part not in artifacts:
                raise ValueError(f"part {part!r} not found in {source!r} "
                                 f"(have {sorted(artifacts)})")
            data = Path(artifacts[part]).read_bytes()
        else:
            data = self._one_artifact(tmp, fmt).read_bytes()
        return f"{base_name}.{fmt}", _content_type(fmt), data

    def _export_assembly_step(self, source: str, base_name: str,
                              tmp: Path) -> tuple[str, str, bytes]:
        """Compose the assembly and return its AP242 STEP bytes."""
        from ncad.assembly.assembly_builder import AssemblyBuilder

        AssemblyBuilder(self._kernel).assemble(source, str(tmp))
        step = self._one_artifact(tmp, "step")
        return f"{base_name}.step", _content_type("step"), step.read_bytes()

    def _motion_assembly_path(self, motion_source: str) -> str:
        """Resolve the assembly document a motion study drives (relative to the motion doc).

        A ``.motion.hocon`` names the assembly it drives in its ``motion.assembly`` field; export
        composes THAT assembly (the motion doc itself is not an assembly document). Mirrors how
        MotionBuilder locates the mechanism before solving. Raises ValueError on a malformed doc.
        """
        import os

        from ncad.spec.spec_loader import SpecLoader

        document = SpecLoader().load(motion_source)
        motion = document.get("motion")
        if not isinstance(motion, dict) or not isinstance(motion.get("assembly"), str):
            raise ValueError(f"motion doc {motion_source!r} has no 'motion.assembly' reference")
        assembly_path = os.path.join(os.path.dirname(os.path.abspath(motion_source)),
                                     motion["assembly"])
        if not os.path.isfile(assembly_path):
            raise ValueError(f"motion references a missing assembly: {motion['assembly']!r}")
        return assembly_path

    def _export_robot(self, source: str, fmt: str, base_name: str,
                      tmp: Path) -> tuple[str, str, bytes]:
        """Export the robot (+ per-link meshes) and return a zip of the artifact + meshes/."""
        from ncad.robotics import RobotModelBuilder
        from ncad.robotics.robot_format import robot_writer

        model, _ = RobotModelBuilder(self._kernel).build(source, str(tmp))
        writer, extension = robot_writer(fmt)
        artifact = tmp / f"{model.name}.{extension}"
        artifact.write_text(writer.to_xml(model), encoding="utf-8")
        # A robot is the artifact + its per-link meshes; zip JUST those (the RobotModelBuilder also
        # drops a static .assembly.json/.step in tmp, which are not part of the robot download).
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(artifact, artifact.name)
            meshes = tmp / "meshes"
            for mesh in sorted(meshes.glob("*")) if meshes.is_dir() else []:
                if mesh.is_file():
                    archive.write(mesh, f"meshes/{mesh.name}")
        return f"{base_name}.zip", _content_type("zip"), buffer.getvalue()

    def _one_artifact(self, tmp: Path, ext: str) -> Path:
        """The single ``.ext`` file the build wrote into ``tmp`` (raises if none)."""
        matches = [p for p in tmp.iterdir() if p.suffix.lower() == f".{ext}"]
        if not matches:
            raise ValueError(f"export produced no .{ext} file")
        return matches[0]


def _content_type(fmt: str) -> str:
    """The download MIME type for ``fmt`` (octet-stream fallback)."""
    return _CONTENT_TYPES.get(fmt, "application/octet-stream")
