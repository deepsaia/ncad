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
from ncad.fea.analysis_error import AnalysisError
from ncad.fea.analysis_mesh_writer import AnalysisMeshWriter
from ncad.fea.analysis_spec import AnalysisSpec
from ncad.fea.ccx_runner import CcxRunner
from ncad.fea.deck_writer import DeckWriter
from ncad.fea.fatigue_calculator import FatigueCalculator
from ncad.fea.frd_reader import FrdReader
from ncad.fea.gmsh_mesher import GmshMesher
from ncad.fea.load_glyph_builder import LoadGlyphBuilder
from ncad.fea.surface_extractor import SurfaceExtractor
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
        # Write the part's feature hierarchy sidecar so the viewer's Hierarchy tab has content in
        # Analyze mode (the part is built here internally, so its normal build sidecars are absent).
        _write_hierarchy(part_path, stem, out_dir)

        mesh_inp = os.path.join(out_dir, f"{stem}.mesh.inp")
        groups = _groups(spec)
        try:
            mesh_report = GmshMesher().mesh(step_path, spec.mesh, groups, mesh_inp)
        except ImportError as exc:
            logger.warning("meshing skipped (install ncad[fea]): %s", exc)
            return _skipped(f"gmsh not installed; install ncad[fea] ({exc})")

        material = _resolve_material(part_path, stem)
        # gmsh writes surface groups as 2D CPS6 elements ccx rejects; rewrite them into element
        # *SURFACEs (for pressure/flux) and strip the 2D elements before decking.
        with open(mesh_inp, encoding="utf-8") as handle:
            mesh_text = handle.read()
        rewritten = SurfaceExtractor().rewrite(mesh_text, list(groups))

        # One deck per procedure FAMILY: CalculiX aborts when a structural step and a thermal step
        # are chained in a single deck (an analysis-type switch). Structural steps (static +
        # frequency) chain fine together; thermal steps go in their own deck.
        families = _step_families(spec.steps)
        artifacts, warnings, family_results = [], list(mesh_report.get("warnings", [])), []
        overall = "generated" if families else "skipped"
        for family, steps in families.items():
            deck_path = os.path.join(out_dir, f"{stem}.{family}.inp")
            deck = DeckWriter().write(rewritten["text"], spec, material, element_set=_ELEMENT_SET,
                                      surfaces=rewritten["surfaces"], faces=rewritten["faces"],
                                      steps=steps)
            with open(deck_path, "w", encoding="utf-8") as handle:
                handle.write(deck)
            artifacts.append(deck_path)
            solve = CcxRunner().solve(deck_path, out_dir)
            warnings += solve["skipped"] + solve["reasons"]
            if solve["status"] == "generated":
                family_results.append((family, solve["artifact"]))
            elif solve["status"] != "generated" and overall == "generated":
                overall = solve["status"]

        result = {"status": overall, "artifact": artifacts[0] if artifacts else None,
                  "artifacts": artifacts, "sidecars": {}, "summary": {}, "mesh": mesh_report,
                  "warnings": warnings}
        if family_results:
            result.update(self._read_back(family_results, material, mesh_inp, out_dir, stem,
                                          spec, rewritten["triangles"]))
        return result

    def _read_back(self, family_results: list, material: dict, mesh_inp: str, out_dir: str,
                   stem: str, spec, group_triangles: dict) -> dict:
        """Merge each family's .frd into one summary + field mesh; return the paths + summary."""
        reader = FrdReader()
        merged: dict = {"max_von_mises": 0.0, "max_displacement": 0.0, "frequencies": [],
                        "safety_factor": None}
        primary = None
        nodes: dict = {}
        scalar_fields: dict = {}
        for _family, frd in family_results:
            parsed = reader.read(frd, material)
            _merge_summary(merged, parsed["summary"])
            nodes = nodes or parsed["nodes"]
            scalar_fields.update(reader.scalar_fields(parsed))  # von_mises/displacement/temperature
            if primary is None and parsed["fields"].get("STRESS"):
                primary = parsed          # color the viewer by the structural (stress) result
        primary = primary or reader.read(family_results[0][1], material)
        _run_fatigue(spec.steps, merged, material)
        json_path = os.path.join(out_dir, f"{stem}.analysis.json")
        # The summary sidecar also carries the load case (constraints/loads/steps) so the viewer's
        # Analyze inspector can show WHAT was analyzed, not just the headline scalars.
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump({"summary": merged, "part": spec.part, "mesh": spec.mesh,
                       "constraints": spec.constraints, "loads": spec.loads,
                       "steps": spec.steps}, handle, indent=2)
        vtk_path = os.path.join(out_dir, f"{stem}.analysis.vtk")
        reader.write_vtk(primary, _read_elements(mesh_inp), vtk_path)
        # The viewer colors the boundary surface; ship it (+ per-vertex fields) as a compact JSON
        # so the browser never parses VTK. All families share the mesh's node ordering.
        mesh_json = AnalysisMeshWriter().build(nodes, _read_elements(mesh_inp), scalar_fields)
        # Load glyphs: what forces/BCs act on the model (drawn as arrows/markers in the viewport),
        # so a user sees WHAT produced the stress/displacement/temperature field.
        mesh_json["loads"] = LoadGlyphBuilder().build(spec, group_triangles, nodes)
        mesh_path = os.path.join(out_dir, f"{stem}.analysis.mesh.json")
        with open(mesh_path, "w", encoding="utf-8") as handle:
            json.dump(mesh_json, handle)
        return {"summary": merged,
                "sidecars": {"json": json_path, "vtk": vtk_path, "mesh": mesh_path}}


def _step_families(steps: list) -> dict:
    """Partition steps into procedure FAMILIES that can share one deck.

    ``structural`` (static + frequency) chain safely together; ``thermal`` (heat_transfer) must be
    its own deck (CalculiX aborts when a structural and a thermal step are chained). Preserves
    authored order within each family; families with no steps are omitted.
    """
    families: dict = {}
    for step in steps:
        if step["procedure"] == "fatigue":
            continue   # a post-process, never a CalculiX deck step (see _run_fatigue)
        family = "thermal" if step["procedure"] == "heat_transfer" else "structural"
        families.setdefault(family, []).append(step)
    return families


def _run_fatigue(steps: list, merged: dict, material: dict) -> None:
    """Post-process each fatigue step into the merged summary (cycles + safety + infinite_life).

    A fatigue step's ``of`` must name a static step in ``steps``; its peak stress is the run's
    max von Mises. Raises AnalysisError if ``of`` is not a static step.
    """
    static_names = {s["name"] for s in steps if s["procedure"] == "static"}
    for step in steps:
        if step["procedure"] != "fatigue":
            continue
        if step["of"] not in static_names:
            raise AnalysisError(
                f"fatigue step {step['name']!r} 'of' {step['of']!r} is not a static step")
        result = FatigueCalculator().life(merged.get("max_von_mises", 0.0), step["ratio"], material)
        merged["cycles_to_failure"] = result["cycles_to_failure"]
        merged["fatigue_safety_factor"] = result["fatigue_safety_factor"]
        merged["infinite_life"] = result["infinite_life"]
        merged["alternating_stress"] = result["alternating_stress"]
        merged["mean_stress"] = result["mean_stress"]


def _merge_summary(merged: dict, summary: dict) -> None:
    """Accumulate a family's summary into the merged scalars (max stress/disp, freqs, SF)."""
    merged["max_von_mises"] = max(merged["max_von_mises"], summary.get("max_von_mises", 0.0))
    merged["max_displacement"] = max(merged["max_displacement"],
                                     summary.get("max_displacement", 0.0))
    merged["frequencies"] = merged["frequencies"] or summary.get("frequencies", [])
    if summary.get("safety_factor") is not None:
        existing = merged["safety_factor"]
        merged["safety_factor"] = (summary["safety_factor"] if existing is None
                                   else min(existing, summary["safety_factor"]))


def _write_hierarchy(part_path: str, stem: str, out_dir: str) -> None:
    """Write ``<stem>.hierarchy.json`` (the part's display feature tree) for the viewer."""
    from ncad.build.hierarchy_builder import HierarchyBuilder

    document = SpecLoader().load(part_path)
    parts = document.get("parts") or {}
    part = parts.get(stem) or next(iter(parts.values()), None)
    part_name = stem if stem in parts else next(iter(parts), stem)
    if part is None:
        return
    tree = HierarchyBuilder().hierarchy(part_name, part)
    with open(os.path.join(out_dir, f"{stem}.hierarchy.json"), "w", encoding="utf-8") as handle:
        json.dump(tree, handle, indent=2)


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
    """Map every constraint + load name (top-level and step-nested) to its ``where`` selector.

    Every BC/load that targets a face needs a named surface group in the mesh; gravity (a body
    force) and a step's own nested thermal loads are all covered so the deck never references an
    undefined set. Gravity carries no ``where`` and is skipped.
    """
    groups: dict = {}
    for constraint in spec.constraints:
        groups[constraint["name"]] = constraint["where"]
    for load in spec.loads:
        if "where" in load:
            groups[load["name"]] = load["where"]
    for step in spec.steps:
        for load in step.get("loads", []):
            if "where" in load:
                groups[load["name"]] = load["where"]
    return groups


def _read_elements(mesh_inp: str) -> list:
    """Read the VOLUME (C3D4/C3D10) element connectivity from the gmsh mesh .inp.

    The mesh .inp also carries gmsh's 2D boundary elements (CPS6); those are skipped so the
    boundary-surface extraction sees only tets (a stray 2D element would corrupt the face count).
    """
    elements: list = []
    reading = False
    with open(mesh_inp, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.upper().startswith("*ELEMENT"):
                reading = "C3D" in stripped.upper().replace(" ", "")
                continue
            if stripped.startswith("*"):
                reading = False
                continue
            if reading and stripped:
                parts = [int(p) for p in stripped.rstrip(",").split(",") if p.strip()]
                elements.append(parts[1:])  # drop the element id, keep node ids
    return elements


def _skipped(reason: str) -> dict:
    """A skipped run report (a missing external tool), carrying the reason as a warning."""
    return {"status": "skipped", "artifact": None, "sidecars": {}, "summary": {},
            "mesh": {}, "warnings": [reason]}
