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
import time
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
        started = time.perf_counter()
        try:
            build_result = builder.build_file(resolved, self._models_dir)
        except (OSError, RuntimeError) as exc:
            raise BuildError(str(exc)) from exc
        build_ms = (time.perf_counter() - started) * 1000.0
        # A design-invalid document no longer raises: it returns error diagnostics + no artifacts.
        diagnostics = [d.to_dict() for d in build_result["diagnostics"]]
        artifacts = build_result["artifacts"]
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
        logger.info("built %s from %s in %.1f ms (%d diagnostic(s))", built, spec, build_ms,
                    len(diagnostics))
        return {"built": built, "build_ms": round(build_ms, 1), "diagnostics": diagnostics}

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
        started = time.perf_counter()
        try:
            result = AssemblyBuilder(Build123dKernel()).assemble(resolved, self._models_dir)
        except (ValueError, OSError, RuntimeError) as exc:
            raise BuildError(str(exc)) from exc
        build_ms = (time.perf_counter() - started) * 1000.0
        name = os.path.basename(result["sidecar"])[: -len(".assembly.json")]
        logger.info("assembled %s from %s (%d issues) in %.1f ms",
                    name, spec, len(result["issues"]), build_ms)
        return {"assembled": name, "issues": result["issues"], "build_ms": round(build_ms, 1)}

    def validate(self, spec: str) -> dict:
        """Validate a document spec WITHOUT building; return the ValidationReport dict.

        Resolves the spec by the same allow-rules as build/assemble/motion (part, else assembly,
        else motion). Raises BuildError only for a disallowed/unresolvable spec; a valid-but-broken
        document returns ``ok=False`` + diagnostics (never raises for a bad design).
        """
        from ncad.diagnostics.document_validator import DocumentValidator
        from ncad.params.function_registry import FunctionRegistry
        from ncad.params.param_resolver import ParamResolver
        from ncad.spec.spec_loader import SpecLoader

        resolved = (self._allowed_path(spec) or self._allowed_assembly_path(spec)
                    or self._allowed_motion_path(spec))
        if resolved is None:
            raise BuildError(f"spec not allowed: {spec}")
        document = SpecLoader().load(resolved)
        # Resolve parameter expressions before validating (a field like distance = "${t}" must
        # become a number before the schema type-checks it), matching the build path.
        expanded = ParamResolver(FunctionRegistry.with_defaults()).resolve_document(document)
        report = DocumentValidator(base_dir=os.path.dirname(resolved)).validate(expanded)
        return report.to_dict()

    def _allowed_path(self, spec: str) -> str | None:
        """Resolve ``spec`` if under examples or a recorded meta source, else None."""
        under_examples = self._spec_catalog.resolve(spec)
        if under_examples is not None:
            return under_examples
        for model in self._model_catalog.models_with_sources():
            if model["source"] == spec and os.path.isfile(spec):
                return spec
        return None

    def build_motion(self, spec: str) -> dict:
        """Build a motion study ``spec`` (drives its referenced assembly + writes a trajectory).

        :return: ``{"assembled": <assembly_name>, "issues": [...]}`` (the trajectory sidecar sits
            beside the assembly scene as <assembly_name>.motion.json).
        :raises BuildError: If the spec is not allowed or the motion build fails.
        """
        from ncad.assembly.motion_builder import MotionBuilder
        from ncad.kernel.build123d_kernel import Build123dKernel

        resolved = self._allowed_motion_path(spec)
        if resolved is None:
            raise BuildError(f"motion spec not allowed: {spec}")
        started = time.perf_counter()
        try:
            result = MotionBuilder(Build123dKernel()).build(resolved, self._models_dir)
        except (ValueError, OSError, RuntimeError) as exc:
            raise BuildError(str(exc)) from exc
        build_ms = (time.perf_counter() - started) * 1000.0
        name = os.path.basename(result["sidecar"])[: -len(".assembly.json")]
        issues = result["issues"]
        # The trajectory sidecar is None when the motion solve failed (a bad material, an unresolved
        # connector, a solver error): the assembly scene still built, but there is NO motion. Say so
        # honestly - "built" is only truthful when a trajectory was actually produced.
        if result.get("motion"):
            logger.info("motion-built %s from %s (%d issue(s)) in %.1f ms",
                        name, spec, len(issues), build_ms)
        else:
            logger.warning("motion solve produced NO trajectory for %s from %s (%d issue(s)) in "
                           "%.1f ms; the assembly scene built but the motion did not", name, spec,
                           len(issues), build_ms)
        return {"assembled": name, "issues": issues, "motion": bool(result.get("motion")),
                "build_ms": round(build_ms, 1)}

    def _allowed_motion_path(self, spec: str) -> str | None:
        """Resolve a motion ``spec`` if under examples or a recorded trajectory source, else None.

        Regenerate passes the source recorded in an existing trajectory sidecar (an absolute path),
        which is not under examples; accept it when a built trajectory records it (mirrors the
        assembly rule, so a reload can regenerate a motion study).
        """
        under_examples = self._spec_catalog.resolve(spec)
        if under_examples is not None:
            return under_examples
        for name in self._model_catalog.motion_names():
            path = self._model_catalog.resolve_motion(name)
            if path is None:
                continue
            with open(path, encoding="utf-8") as handle:
                source = json.load(handle).get("source")
            if source == spec and os.path.isfile(spec):
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
