"""Load, validate, build, and export a feature-tree document.

Ties the reuse-core spec layer (loader + DocumentValidator) to the pure Builder and the kernel's
export. The agent-facing file entry (:meth:`build_file`) returns diagnostics as DATA and never
raises for a bad design; the strict programmatic entries (:meth:`build` and the assembly-support
resolvers) raise on an invalid document, since their callers have no diagnostics channel.
Per-feature build problems ride the same Diagnostic envelope (design §10).
"""

import json
import logging
import os
from typing import Any

from ncad.build.builder import Builder
from ncad.build.feature_cache import FeatureCache
from ncad.build.hierarchy_builder import HierarchyBuilder
from ncad.build.material_resolver import MaterialResolver
from ncad.build.sketch_status_sidecar import SketchStatusSidecar
from ncad.diagnostics.diagnostic import Diagnostic
from ncad.diagnostics.document_validator import DocumentValidator
from ncad.kernel.kernel import Kernel
from ncad.ops.op_registry import OpRegistry
from ncad.ops.op_result import OpResult
from ncad.params.function_registry import FunctionRegistry
from ncad.params.param_resolver import ParamResolver
from ncad.refs.attribute_model import AttributeModel
from ncad.spec.material_library import MaterialLibrary
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_ELEMENTMAP_SUFFIX = ".elementmap.json"
_HIERARCHY_SUFFIX = ".hierarchy.json"
# Export format -> file extension. glb is the display mesh (viewer); step is the exact
# B-rep for CAD interchange (design §14).
_FORMAT_EXTENSIONS = {"glb": "glb", "step": "step"}


def resolve_formats(formats: tuple[str, ...]) -> tuple[str, ...]:
    """Validate requested export formats; raise ValueError listing supported ones.

    Public because it is the shared format-validation contract: the CLI's --format parser
    (build/__main__.py) reuses it so the supported set is single-sourced.
    """
    unknown = [f for f in formats if f not in _FORMAT_EXTENSIONS]
    if unknown:
        supported = ", ".join(sorted(_FORMAT_EXTENSIONS))
        raise ValueError(f"unsupported export format(s) {unknown}; supported: {supported}")
    return tuple(formats)


class DocumentBuilder:
    """Builds every part in a document into geometry, optionally exporting glTF."""

    def __init__(self, kernel: Kernel) -> None:
        """:param kernel: Geometry backend used by the Builder and for export."""
        self._kernel = kernel
        self._cache = FeatureCache()
        self._builder = Builder(kernel, OpRegistry.with_defaults(), cache=self._cache)
        self._validator = DocumentValidator()
        self._hierarchy = HierarchyBuilder()
        self._loader = SpecLoader()
        self._resolver = ParamResolver(FunctionRegistry.with_defaults())
        self._rebuild_stats: dict[str, dict[str, bool]] = {}

    def build(self, document: dict) -> dict[str, OpResult]:
        """Resolve expressions, validate, and build each part (incremental via cache).

        The cache persists across calls on this instance, so re-building an edited
        document re-executes only the dirty suffix (design section 4). Per-part cache
        hit/miss stats are captured for the last call (see :meth:`rebuild_stats`).

        :param document: A loaded feature-tree document dict.
        :return: Map from part name to its :class:`OpResult`.
        :raises ExpressionError: If a parameter expression is malformed.
        :raises ValueError: If the resolved document fails schema validation.
        """
        resolved = self._resolve_and_validate(document)
        results: dict[str, OpResult] = {}
        self._rebuild_stats = {}
        for name, part in resolved["parts"].items():
            logger.debug("building part %s", name)
            self._cache.reset_stats()
            result, _, _ = self._builder.build_part_mapped(part)
            results[name] = result
            self._rebuild_stats[name] = self._cache.stats()
        return results

    def rebuild_stats(self) -> dict[str, dict[str, bool]]:
        """Per-part cache hit/miss map from the last build call."""
        return {name: dict(stats) for name, stats in self._rebuild_stats.items()}

    def build_file_document(self, path: str) -> dict[str, OpResult]:
        """Load the document at ``path`` and build it (no export)."""
        return self.build(self._loader.load(path))

    def build_file(self, path: str, out_dir: str,
                   formats: tuple[str, ...] = ("glb",),
                   name_prefix: str = "") -> dict[str, Any]:
        """Load, build, and export each part to ``<out_dir>/<prefix><part>.<ext>`` per format.

        Also writes each part's element-map / hierarchy / status sidecars beside the
        artifacts. ``formats`` selects the export format(s) (``glb`` and/or ``step``); the
        default keeps the viewer's glb-only path unchanged. glb is the display mesh; step
        is the exact B-rep for CAD interchange (design §14).

        ``name_prefix`` namespaces the written artifact + sidecar basenames (default ""
        keeps the bare ``<part>`` names). Assembly composition passes the source document's
        stem so two mechanisms that both define a part named ``stand`` write distinct
        ``<doc>__stand.glb`` files into the shared output dir instead of clobbering one
        ``stand.glb``. The artifacts map is still keyed by the bare part name.

        This is the agent-facing entry: a bad DESIGN is reported as data, not raised. On any
        error-severity diagnostic (schema/semantic) geometry is skipped and ``artifacts`` is empty;
        warnings/info do not block. Per-feature build failures ride the same Diagnostic envelope.

        :return: ``{"artifacts": {part: primary_artifact_path}, "diagnostics": [Diagnostic, ...]}``.
        """
        resolved_formats = resolve_formats(formats)
        os.makedirs(out_dir, exist_ok=True)
        document = self._loader.load(path)
        resolved, diagnostics = self._resolve_with_diagnostics(document)
        if any(d.severity == "error" for d in diagnostics):
            # The document is invalid: skip geometry entirely and hand the errors back as data.
            return {"artifacts": {}, "diagnostics": diagnostics}
        # The material library reads the RAW document (materials / materials_library), resolved
        # relative to the document's own directory. Bodies get their material via created_by.
        material_library = MaterialLibrary(document, base_dir=os.path.dirname(path))
        artifacts: dict[str, str] = {}
        for name, part in resolved["parts"].items():
            stem = f"{name_prefix}{name}"
            result, element_map, statuses = self._builder.build_part_mapped(part)
            # Build-stage issues ride the same envelope as schema/semantic ones (design §10).
            diagnostics.extend(issue.to_diagnostic() for issue in result.issues)
            if result.shape is None:
                reasons = "; ".join(f"[{i.node_id}] {i.message}" for i in result.issues
                                    if i.level == "error") or "no error detail reported"
                logger.warning("part %s did not build; skipping export. reason(s): %s",
                               name, reasons)
                continue
            bodies = self._body_materials(result.shape, part, material_library)
            # The authored per-body appearance color is model data, so export writes it (the
            # glTF baseColorFactor) - default per-body colors then port to any renderer, not
            # just our viewer overlay. Only bodies with an authored appearance.color are set.
            body_colors = {b["id"]: _rgba(b["appearance_color"]) for b in bodies
                           if b.get("appearance_color") is not None}
            written: list[str] = []
            for fmt in resolved_formats:
                artifact_path = os.path.join(out_dir, f"{stem}.{_FORMAT_EXTENSIONS[fmt]}")
                self._kernel.export(result.shape, artifact_path, body_colors=body_colors)
                written.append(artifact_path)
            self._write_element_map(element_map, out_dir, stem, bodies, result.shape)
            self._write_hierarchy(part, out_dir, stem, statuses, bodies)
            SketchStatusSidecar(out_dir).write(stem, statuses)
            for status in statuses:
                logger.info("sketch %s: %s-constrained (dof %d)%s", status.feature_id,
                            status.status, status.dof,
                            f" {status.failing_ids}" if status.failing_ids else "")
            artifacts[name] = written[0]
        return {"artifacts": artifacts, "diagnostics": diagnostics}

    def write_element_maps(self, document: dict, out_dir: str) -> dict[str, str]:
        """Build each part and write its ``<part>.elementmap.json`` sidecar.

        For backends that cannot export geometry (the fake kernel in tests), this
        produces the element-map sidecars without exporting a glb.

        :return: Map from part name to the written sidecar path.
        """
        os.makedirs(out_dir, exist_ok=True)
        resolved = self._resolve_and_validate(document)
        written: dict[str, str] = {}
        for name, part in resolved["parts"].items():
            _, element_map, _ = self._builder.build_part_mapped(part)
            # No bodies map here: this element-map-only path does not feed the viewer's
            # material coloring, so records get material=null (bodies defaults to None).
            written[name] = self._write_element_map(element_map, out_dir, name)
        return written

    def resolve_part_builds(self, path: str) -> dict[str, tuple]:
        """Return ``{part_name: (shape, resolver)}`` for the document at ``path``.

        Used by the assembly layer for interference + mass + STEP: it needs each part's built
        SHAPE plus a MaterialResolver over the part's materials. Reuses the feature cache (built
        once per file), like resolve_part_elements. ``shape`` is None for a part that did not build.
        """
        document = self._loader.load(path)
        resolved = self._resolve_and_validate(document)
        material_library = MaterialLibrary(document, base_dir=os.path.dirname(path))
        out: dict[str, tuple] = {}
        for name, part in resolved["parts"].items():
            result, _, _ = self._builder.build_part_mapped(part)
            resolver = MaterialResolver(part, material_library)
            out[name] = (result.shape, resolver)
        return out

    def resolve_part_elements(self, path: str) -> dict[str, tuple[dict, list]]:
        """Return ``{part_name: (resolved_part_dict, elements)}`` for the document at ``path``.

        Used by the assembly layer to resolve a part's mate connectors against its element map.
        Reuses the feature cache, so calling this after :meth:`build_file` on the same instance
        re-executes nothing (the element map comes straight from the cached build).
        """
        resolved = self._resolve_and_validate(self._loader.load(path))
        out: dict[str, tuple[dict, list]] = {}
        for name, part in resolved["parts"].items():
            _, element_map, _ = self._builder.build_part_mapped(part)
            out[name] = (part, element_map.elements())
        return out

    def _resolve_with_diagnostics(self, document: dict) -> tuple[dict, list[Diagnostic]]:
        """Resolve expressions + run static validation; return (resolved, diagnostics).

        Never raises for a bad DESIGN (design errors are data now, per the agent-facing contract):
        the file entry skips geometry when any error-severity diagnostic is present. A malformed
        parameter EXPRESSION still raises (a contract error, not a design issue) from resolve.
        """
        resolved = self._resolver.resolve_document(document)
        report = self._validator.validate(resolved)
        return resolved, report.diagnostics

    def _resolve_and_validate(self, document: dict) -> dict:
        """Resolve + validate for the strict programmatic entries; raise on any error diagnostic.

        :meth:`build` and the assembly-support resolvers have no diagnostics channel, so an invalid
        document is surfaced as a ValueError there (unchanged contract). :meth:`build_file` uses
        :meth:`_resolve_with_diagnostics` directly and returns the diagnostics instead.
        """
        resolved, diagnostics = self._resolve_with_diagnostics(document)
        errors = [d for d in diagnostics if d.severity == "error"]
        if errors:
            rendered = "; ".join(f"{d.location}: {d.message}" for d in errors)
            raise ValueError(f"document failed validation: {rendered}")
        return resolved

    def _write_element_map(self, element_map, out_dir: str, name: str,
                           bodies: Any = None, shape: Any = None) -> str:
        """Write ``<name>.elementmap.json`` and return its path.

        ``bodies`` (``{id, material, appearance_color}`` per built body) stamps each element's
        material by its body_id, so the viewer can color faces by material. ElementMap stays
        material-free; material is document data resolved here. ``shape`` (the built result)
        adds a ``meshes`` list: one ``{body_id, material, appearance_color}`` per exported glTF
        mesh in export order, so the viewer maps mesh index -> body -> material positionally
        (glTF mesh names do not survive the loader).
        """
        by_body = {b["id"]: b for b in (bodies or [])}
        records = element_map.to_sidecar()
        for rec in records:
            body = by_body.get(rec.get("body_id"))
            rec["material"] = body["material"] if body else None
            rec["appearance_color"] = body.get("appearance_color") if body else None
        meshes = []
        if shape is not None:
            for body_id in self._kernel.mesh_body_ids(shape):
                body = by_body.get(body_id)
                meshes.append({"body_id": body_id,
                               "material": body["material"] if body else None,
                               "appearance_color": body.get("appearance_color") if body
                               else None})
        path = os.path.join(out_dir, f"{name}{_ELEMENTMAP_SUFFIX}")
        payload = {"attribute_model_version": AttributeModel.VERSION,
                   "elements": records, "meshes": meshes}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        return path

    def _write_hierarchy(self, part: dict, out_dir: str, name: str,
                         statuses: Any = None, bodies: Any = None) -> str:
        """Write ``<name>.hierarchy.json`` (the display feature tree) and return its path.

        ``statuses`` are stamped onto sketch nodes so the tree shows constraint status inline;
        ``bodies`` (``{id, material}`` per built body) become the trailing Bodies group.
        """
        path = os.path.join(out_dir, f"{name}{_HIERARCHY_SUFFIX}")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self._hierarchy.hierarchy(name, part, statuses=statuses, bodies=bodies),
                      handle)
        return path

    def _body_materials(self, shape: Any, part: dict,
                        material_library: MaterialLibrary) -> list[dict]:
        """One ``{id, material, appearance_color}`` per built body, resolved via created_by.

        Material is optional: a body with no resolvable material has ``material=None`` (and no
        appearance color). ``appearance_color`` is the material's authored
        ``mat_data.appearance.color`` if present, else None. Never raises; display-only. Feeds
        both the hierarchy Bodies group (reads id/material) and the element-map material stamp.
        """
        resolver = MaterialResolver(part, material_library)
        out: list[dict] = []
        for body in self._kernel.bodies(shape):
            name = resolver.material_name(body)
            color = None
            if name is not None:
                mat = resolver.for_body(body) or {}
                color = mat.get("appearance", {}).get("color")
            out.append({"id": body.id, "material": name, "appearance_color": color})
        return out


def _rgba(color: Any) -> tuple[float, float, float, float]:
    """Normalize an authored appearance color to an (r, g, b, a) tuple in 0..1.

    Accepts a 3-tuple/list (rgb, alpha defaults to 1) or a 4-tuple (rgba). Values are assumed
    already in 0..1 (the authored appearance convention).
    """
    vals = [float(c) for c in color]
    if len(vals) == 3:
        vals.append(1.0)
    return (vals[0], vals[1], vals[2], vals[3])
