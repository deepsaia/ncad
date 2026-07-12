"""Run a spec build on behalf of the viewer, safely and with metadata.

The only viewer unit that touches the geometry kernel. It (1) checks the requested spec
is allowed (resolves under the examples directory, or equals a source already recorded
in a model's meta sidecar), (2) runs the existing DocumentBuilder build path, and
(3) writes a meta sidecar per built model so it can be regenerated later. Failures are
raised as a typed BuildError; the server turns that into a JSON error response.
"""

import json
import logging
import os
from collections.abc import Callable

from ncad.viewer.model_catalog import ModelCatalog
from ncad.viewer.model_metadata import ModelMetadata
from ncad.viewer.spec_catalog import SpecCatalog

logger = logging.getLogger(__name__)


class BuildError(Exception):
    """A build request that was disallowed or that failed to produce geometry."""


class BuildService:
    """Validates, runs, and records a viewer-triggered spec build."""

    def __init__(
        self,
        examples_dir: str,
        models_dir: str,
        builder_factory: Callable,
        *,
        meta: ModelMetadata | None = None,
        clock: Callable[[], str] | None = None,
        versions: dict | None = None,
    ) -> None:
        """:param examples_dir: Directory of allowed example specs.
        :param models_dir: Output directory for built models.
        :param builder_factory: Zero-arg callable returning an object with
            ``build_file(path, out_dir) -> dict[str, str]``.
        :param meta: ModelMetadata writer (defaults to one over ``models_dir``).
        :param clock: Zero-arg callable returning an ISO-8601 timestamp string.
        :param versions: Dict with ``ncad`` and ``kernel`` version strings.
        """
        self._examples_dir = os.path.abspath(examples_dir)
        self._models_dir = os.path.abspath(models_dir)
        self._builder_factory = builder_factory
        self._spec_catalog = SpecCatalog(examples_dir)
        self._model_catalog = ModelCatalog(models_dir)
        self._meta = meta or ModelMetadata(models_dir)
        self._clock = clock
        self._versions = versions or {"ncad": "unknown", "kernel": "unknown"}

    def build(self, spec: str) -> dict:
        """Build ``spec`` (a relative example path or a recorded meta source).

        :return: ``{"built": [model_name, ...]}``.
        :raises BuildError: If the spec is not allowed or the build fails.
        """
        resolved = self._allowed_path(spec)
        if resolved is None:
            raise BuildError(f"spec not allowed: {spec}")
        builder = self._builder_factory()
        try:
            artifacts = builder.build_file(resolved, self._models_dir)
        except (ValueError, OSError, RuntimeError) as exc:
            raise BuildError(str(exc)) from exc
        built = [os.path.basename(path) for path in artifacts.values()]
        built_at = self._clock() if self._clock is not None else ""
        for name in built:
            self._meta.write(
                name,
                source=spec,
                built_at=built_at,
                ncad_version=self._versions["ncad"],
                kernel_version=self._versions["kernel"],
            )
        logger.info("built %s from %s", built, spec)
        return {"built": built}

    def assemble(self, spec: str) -> dict:
        """Compose an assembly document ``spec`` into a scene sidecar.

        :return: ``{"assembled": <assembly_name>, "issues": [...]}``.
        :raises BuildError: If the spec is not allowed or composition fails.
        """
        from ncad.assembly.assembly_builder import AssemblyBuilder
        from ncad.kernel.build123d_kernel import Build123dKernel

        resolved = self._allowed_assembly_path(spec)
        if resolved is None:
            raise BuildError(f"assembly spec not allowed: {spec}")
        try:
            result = AssemblyBuilder(Build123dKernel()).assemble(resolved, self._models_dir)
        except (ValueError, OSError, RuntimeError) as exc:
            raise BuildError(str(exc)) from exc
        name = os.path.basename(result["sidecar"])[: -len(".assembly.json")]
        logger.info("assembled %s from %s (%d issues)", name, spec, len(result["issues"]))
        return {"assembled": name, "issues": result["issues"]}

    def _allowed_path(self, spec: str) -> str | None:
        """Resolve ``spec`` if under examples or a recorded meta source, else None."""
        under_examples = self._spec_catalog.resolve(spec)
        if under_examples is not None:
            return under_examples
        for model in self._model_catalog.models_with_sources():
            if model["source"] == spec and os.path.isfile(spec):
                return spec
        return None

    def _allowed_assembly_path(self, spec: str) -> str | None:
        """Resolve an assembly ``spec`` if under examples or a recorded scene source, else None.

        Regenerate passes the source recorded in an existing scene sidecar (an absolute path),
        which is not under examples; accept it when a built scene records it (mirrors the part
        meta-source rule, so a reload can regenerate).
        """
        under_examples = self._spec_catalog.resolve(spec)
        if under_examples is not None:
            return under_examples
        for name in self._model_catalog.assembly_names():
            path = self._model_catalog.resolve_assembly(name)
            if path is None:
                continue
            with open(path, encoding="utf-8") as handle:
                source = json.load(handle).get("source")
            if source == spec and os.path.isfile(spec):
                return spec
        return None
