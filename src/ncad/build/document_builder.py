"""Load, validate, build, and export a feature-tree document.

Ties the reuse-core spec layer (loader + schema validator) to the pure Builder and the
kernel's export. Schema-invalid input is a contract error and raises; per-feature build
problems are returned as issues on each part's OpResult (design §10).
"""

import json
import logging
import os

from ncad.build.builder import Builder
from ncad.build.feature_cache import FeatureCache
from ncad.build.hierarchy_builder import HierarchyBuilder
from ncad.kernel.kernel import Kernel
from ncad.ops.op_registry import OpRegistry
from ncad.ops.op_result import OpResult
from ncad.params.function_registry import FunctionRegistry
from ncad.params.param_resolver import ParamResolver
from ncad.refs.attribute_model import AttributeModel
from ncad.spec.dependency_validator import DependencyValidator
from ncad.spec.feature_id_validator import FeatureIdValidator
from ncad.spec.schema_validator import SchemaValidator
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_ELEMENTMAP_SUFFIX = ".elementmap.json"
_HIERARCHY_SUFFIX = ".hierarchy.json"


class DocumentBuilder:
    """Builds every part in a document into geometry, optionally exporting glTF."""

    def __init__(self, kernel: Kernel) -> None:
        """:param kernel: Geometry backend used by the Builder and for export."""
        self._kernel = kernel
        self._cache = FeatureCache()
        self._builder = Builder(kernel, OpRegistry.with_defaults(), cache=self._cache)
        self._validator = SchemaValidator()
        self._id_validator = FeatureIdValidator()
        self._dependency_validator = DependencyValidator()
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
            result, _ = self._builder.build_part_mapped(part)
            results[name] = result
            self._rebuild_stats[name] = self._cache.stats()
        return results

    def rebuild_stats(self) -> dict[str, dict[str, bool]]:
        """Per-part cache hit/miss map from the last build call."""
        return {name: dict(stats) for name, stats in self._rebuild_stats.items()}

    def build_file_document(self, path: str) -> dict[str, OpResult]:
        """Load the document at ``path`` and build it (no export)."""
        return self.build(self._loader.load(path))

    def build_file(self, path: str, out_dir: str) -> dict[str, str]:
        """Load, build, and export each part to ``<out_dir>/<part>.glb``.

        Also writes each part's ``<part>.elementmap.json`` sidecar beside the glb.

        :return: Map from part name to the written ``.glb`` path.
        """
        os.makedirs(out_dir, exist_ok=True)
        resolved = self._resolve_and_validate(self._loader.load(path))
        artifacts: dict[str, str] = {}
        for name, part in resolved["parts"].items():
            result, element_map = self._builder.build_part_mapped(part)
            if result.shape is None:
                logger.warning("part %s did not build; skipping export", name)
                continue
            glb_path = os.path.join(out_dir, f"{name}.glb")
            self._kernel.export(result.shape, glb_path)
            self._write_element_map(element_map, out_dir, name)
            self._write_hierarchy(part, out_dir, name)
            artifacts[name] = glb_path
        return artifacts

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
            _, element_map = self._builder.build_part_mapped(part)
            written[name] = self._write_element_map(element_map, out_dir, name)
        return written

    def _resolve_and_validate(self, document: dict) -> dict:
        """Resolve expressions and run schema + feature-id validation (raises on failure)."""
        resolved = self._resolver.resolve_document(document)
        issues = self._validator.validate(resolved)
        if issues:
            rendered = "; ".join(f"{issue.location}: {issue.message}" for issue in issues)
            raise ValueError(f"document failed schema validation: {rendered}")
        id_issues = self._id_validator.validate(resolved)
        if id_issues:
            rendered = "; ".join(f"{i.location}: {i.message}" for i in id_issues)
            raise ValueError(f"document has duplicate feature ids: {rendered}")
        dep_issues = self._dependency_validator.validate(resolved)
        if dep_issues:
            rendered = "; ".join(f"{i.location}: {i.message}" for i in dep_issues)
            raise ValueError(f"document has dependency errors: {rendered}")
        return resolved

    @staticmethod
    def _write_element_map(element_map, out_dir: str, name: str) -> str:
        """Write ``<name>.elementmap.json`` and return its path."""
        path = os.path.join(out_dir, f"{name}{_ELEMENTMAP_SUFFIX}")
        payload = {"attribute_model_version": AttributeModel.VERSION,
                   "elements": element_map.to_sidecar()}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        return path

    def _write_hierarchy(self, part: dict, out_dir: str, name: str) -> str:
        """Write ``<name>.hierarchy.json`` (the display feature tree) and return its path."""
        path = os.path.join(out_dir, f"{name}{_HIERARCHY_SUFFIX}")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self._hierarchy.hierarchy(name, part), handle)
        return path
