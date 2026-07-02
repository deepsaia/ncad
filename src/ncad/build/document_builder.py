"""Load, validate, build, and export a feature-tree document.

Ties the reuse-core spec layer (loader + schema validator) to the pure Builder and the
kernel's export. Schema-invalid input is a contract error and raises; per-feature build
problems are returned as issues on each part's OpResult (design §10).
"""

import logging
import os

from ncad.build.builder import Builder
from ncad.kernel.kernel import Kernel
from ncad.ops.op_registry import default_registry
from ncad.ops.op_result import OpResult
from ncad.spec.schema_validator import SchemaValidator
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)


class DocumentBuilder:
    """Builds every part in a document into geometry, optionally exporting glTF."""

    def __init__(self, kernel: Kernel) -> None:
        """:param kernel: Geometry backend used by the Builder and for export."""
        self._kernel = kernel
        self._builder = Builder(kernel, default_registry())
        self._validator = SchemaValidator()
        self._loader = SpecLoader()

    def build(self, document: dict) -> dict[str, OpResult]:
        """Validate ``document`` and build each part.

        :param document: A loaded feature-tree document dict.
        :return: Map from part name to its :class:`OpResult`.
        :raises ValueError: If the document fails schema validation.
        """
        issues = self._validator.validate(document)
        if issues:
            rendered = "; ".join(f"{issue.location}: {issue.message}" for issue in issues)
            raise ValueError(f"document failed schema validation: {rendered}")
        results: dict[str, OpResult] = {}
        for name, part in document["parts"].items():
            logger.debug("building part %s", name)
            results[name] = self._builder.build_part(part)
        return results

    def build_file_document(self, path: str) -> dict[str, OpResult]:
        """Load the document at ``path`` and build it (no export)."""
        return self.build(self._loader.load(path))

    def build_file(self, path: str, out_dir: str) -> dict[str, str]:
        """Load, build, and export each part to ``<out_dir>/<part>.glb``.

        :return: Map from part name to the written ``.glb`` path.
        """
        os.makedirs(out_dir, exist_ok=True)
        results = self.build_file_document(path)
        artifacts: dict[str, str] = {}
        for name, result in results.items():
            if result.shape is None:
                logger.warning("part %s did not build; skipping export", name)
                continue
            glb_path = os.path.join(out_dir, f"{name}.glb")
            self._kernel.export(result.shape, glb_path)
            artifacts[name] = glb_path
        return artifacts
