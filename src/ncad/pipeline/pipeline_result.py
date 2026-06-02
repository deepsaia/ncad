"""Result of a full pipeline run: what was produced and what was found."""

from dataclasses import dataclass

from ncad.validate.issue import Issue


@dataclass(frozen=True)
class PipelineResult:
    """Outcome of running the spine end-to-end for one seed.

    :ivar seed: The seed that produced the spec.
    :ivar name: Base name used for the output files.
    :ivar artifacts: Map of artifact kind -> absolute path (model/bom/plan/spec).
    :ivar bom: The bill-of-materials quantities as a dict.
    :ivar semantic_issues: Semantic validation issues found (empty if clean).
    """

    seed: int
    name: str
    artifacts: dict[str, str]
    bom: dict
    semantic_issues: list[Issue]
