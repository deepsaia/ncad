"""The v1 spine, end to end: generate → validate → build → export.

Ties the units together into one run. Schema validity is a contract the generator must
honor, so a schema failure raises (programmer error). Semantic issues are data — a
spec can be schema-valid yet architecturally questionable — so they are collected and
returned rather than raised (design.md §5).
"""

import json
import logging
import os

from ncad.bom.bom_calculator import BomCalculator
from ncad.build.artifact_exporter import ArtifactExporter
from ncad.generate.generator import Generator
from ncad.kernel.kernel import Kernel
from ncad.pipeline.pipeline_result import PipelineResult
from ncad.spec.schema_validator import SchemaValidator
from ncad.validate.semantic_validator import SemanticValidator

logger = logging.getLogger(__name__)

_SPEC_SUFFIX = ".spec.json"


class SpecContractError(ValueError):
    """Raised when a generated spec fails schema validation (a contract violation)."""


class Pipeline:
    """Runs the full generate→validate→build→export spine for a seed."""

    def __init__(self, kernel: Kernel) -> None:
        """:param kernel: Geometry backend used to build and export the model."""
        self._kernel = kernel
        self._schema_validator = SchemaValidator()
        self._semantic_validator = SemanticValidator()
        self._bom_calculator = BomCalculator()

    def run(
        self, seed: int, params: dict, out_dir: str, name: str | None = None
    ) -> PipelineResult:
        """Generate, validate, build and export a building for ``seed``.

        :param seed: Generation seed.
        :param params: Generator parameters.
        :param out_dir: Directory for the output artifacts (created if absent).
        :param name: Base name for output files; defaults to ``house_seed<seed>``.
        :return: A :class:`PipelineResult` with artifact paths, BOM, and semantic issues.
        :raises SpecContractError: If the generated spec fails schema validation.
        """
        resolved_name = name or f"house_seed{seed}"
        os.makedirs(out_dir, exist_ok=True)

        spec = Generator(params).generate(seed)

        schema_issues = self._schema_validator.validate(spec)
        if schema_issues:
            raise SpecContractError(
                f"generated spec failed schema validation: "
                f"{[f'{i.location}: {i.message}' for i in schema_issues]}"
            )
        semantic_issues = self._semantic_validator.validate(spec)

        spec_path = os.path.join(out_dir, resolved_name + _SPEC_SUFFIX)
        with open(spec_path, "w", encoding="utf-8") as handle:
            json.dump(spec, handle, indent=2, sort_keys=True)

        artifacts = ArtifactExporter(self._kernel).export(spec, out_dir, resolved_name)
        artifacts["spec"] = os.path.abspath(spec_path)

        bom = self._bom_calculator.quantities(spec).as_dict()

        logger.info(
            "pipeline run seed=%d name=%s: %d semantic issue(s)",
            seed,
            resolved_name,
            len(semantic_issues),
        )
        return PipelineResult(
            seed=seed,
            name=resolved_name,
            artifacts=artifacts,
            bom=bom,
            semantic_issues=semantic_issues,
        )
