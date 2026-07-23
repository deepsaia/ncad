"""Orchestrate the structural-FEA seam: an .analysis.hocon load case to solved result sidecars.

The pipeline: resolve + build the referenced part, export its STEP, mesh it (GmshMesher) with one
named group per constraint/load, compose the CalculiX deck (DeckWriter), delegate the solve
(CcxRunner), and parse the results (FrdReader) into ``out/<part>.analysis.json`` (summary) plus
``out/<part>.analysis.vtk`` (the field mesh the viewer colors). Every external-tool absence
degrades to a ``skipped`` report (never a raise): gmsh missing -> skipped at meshing; ccx missing
-> skipped at solve. One class.
"""

import json
import logging
import os

from ncad.build.document_builder import DocumentBuilder
from ncad.fea.analysis_spec import AnalysisSpec
from ncad.fea.ccx_runner import CcxRunner
from ncad.fea.deck_writer import DeckWriter
from ncad.fea.frd_reader import FrdReader
from ncad.fea.gmsh_mesher import GmshMesher
from ncad.spec.material_library import MaterialLibrary
from ncad.spec.spec_loader import SpecLoader
from ncad.spec.spec_reference import SpecReference

logger = logging.getLogger(__name__)

_ELEMENT_SET = "all"


class AnalysisDocument:
    """Runs the whole FEA seam for one .analysis.hocon document, writing result sidecars."""

    def run(self, analysis_path: str, out_dir: str) -> dict:
        """Build, mesh, deck, solve, and read back the analysis at ``analysis_path``.

        :return: ``{status, artifact, sidecars, summary, mesh, warnings}`` where ``status`` is the
            solve status (``generated``/``skipped``/``failed``); ``skipped`` also covers a missing
            gmsh (no meshing) with the reason in ``warnings``.
        """
        os.makedirs(out_dir, exist_ok=True)
        spec = AnalysisSpec(SpecLoader().load(analysis_path))
        part_path = SpecReference().for_doc(spec.part, analysis_path)
        stem = os.path.splitext(os.path.basename(part_path))[0]

        kernel, shape = _build_part(part_path, stem)
        step_path = os.path.join(out_dir, f"{stem}.step")
        kernel.export(shape, step_path)

        mesh_inp = os.path.join(out_dir, f"{stem}.mesh.inp")
        groups = _groups(spec)
        try:
            mesh_report = GmshMesher().mesh(step_path, spec.mesh, groups, mesh_inp)
        except ImportError as exc:
            logger.warning("meshing skipped (install ncad[fea]): %s", exc)
            return _skipped(f"gmsh not installed; install ncad[fea] ({exc})")

        material = _resolve_material(part_path, stem)
        deck_path = os.path.join(out_dir, f"{stem}.inp")
        deck = DeckWriter().write(open(mesh_inp, encoding="utf-8").read(), spec, material,
                                  element_set=_ELEMENT_SET)
        with open(deck_path, "w", encoding="utf-8") as handle:
            handle.write(deck)

        solve = CcxRunner().solve(deck_path, out_dir)
        result = {"status": solve["status"], "artifact": deck_path, "sidecars": {},
                  "summary": {}, "mesh": mesh_report,
                  "warnings": mesh_report.get("warnings", []) + solve["skipped"] + solve["reasons"]}
        if solve["status"] == "generated":
            result.update(self._read_back(solve["artifact"], material, mesh_inp, out_dir, stem))
        return result

    def _read_back(self, frd_path: str, material: dict, mesh_inp: str, out_dir: str,
                   stem: str) -> dict:
        """Parse the .frd and write the summary + field-mesh sidecars; return paths + summary."""
        reader = FrdReader()
        parsed = reader.read(frd_path, material)
        json_path = os.path.join(out_dir, f"{stem}.analysis.json")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump({"summary": parsed["summary"]}, handle, indent=2)
        vtk_path = os.path.join(out_dir, f"{stem}.analysis.vtk")
        reader.write_vtk(parsed, _read_elements(mesh_inp), vtk_path)
        return {"summary": parsed["summary"], "sidecars": {"json": json_path, "vtk": vtk_path}}


def _build_part(part_path: str, stem: str):
    """Build the referenced part and return (kernel, shape); raise if it does not build."""
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builds = DocumentBuilder(kernel).resolve_part_builds(part_path)
    shape = None
    if stem in builds:
        shape = builds[stem][0]
    if shape is None:
        # Fall back to the first part that built (the stem may differ from the part name).
        shape = next((s for s, _ in builds.values() if s is not None), None)
    if shape is None:
        from ncad.fea.analysis_error import AnalysisError
        raise AnalysisError(f"analysis part {part_path!r} produced no solid to mesh")
    return kernel, shape


def _resolve_material(part_path: str, stem: str) -> dict:
    """Resolve the referenced part's material record (part-level default), for the deck."""
    document = SpecLoader().load(part_path)
    library = MaterialLibrary(document, base_dir=os.path.dirname(part_path))
    parts = document.get("parts") or {}
    part = parts.get(stem) or next(iter(parts.values()), {})
    name = part.get("material")
    if name is None or not library.has(name):
        return {"structural": {"youngs_modulus": 200e9, "poisson": 0.3},
                "physical": {"density": 0.0}}
    return library.resolve(name)


def _groups(spec: AnalysisSpec) -> dict:
    """Map each constraint + top-level load name to its ``where`` selector (gravity has none)."""
    groups: dict = {}
    for constraint in spec.constraints:
        groups[constraint["name"]] = constraint["where"]
    for load in spec.loads:
        if "where" in load:
            groups[load["name"]] = load["where"]
    return groups


def _read_elements(mesh_inp: str) -> list:
    """Read C3D4/C3D10 element connectivity (node id lists) from the gmsh mesh .inp."""
    elements: list = []
    in_elements = False
    with open(mesh_inp, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.upper().startswith("*ELEMENT"):
                in_elements = True
                continue
            if stripped.startswith("*"):
                in_elements = False
                continue
            if in_elements and stripped:
                parts = [int(p) for p in stripped.rstrip(",").split(",") if p.strip()]
                elements.append(parts[1:])  # drop the element id, keep node ids
    return elements


def _skipped(reason: str) -> dict:
    """A skipped run report (a missing external tool), carrying the reason as a warning."""
    return {"status": "skipped", "artifact": None, "sidecars": {}, "summary": {},
            "mesh": {}, "warnings": [reason]}
