"""Brief fixtures must compile to schema- and semantically-valid specs.

Mirrors test_fixture_specs.py (which guards full-spec fixtures): every brief under
tests/fixtures/briefs/ is loaded, compiled via SpecCompiler, and validated. New briefs
are picked up automatically. This is the regression net for the agent-authorable layer.
"""

from pathlib import Path

import pytest

from ncad.compile.spec_compiler import SpecCompiler
from ncad.spec.schema_validator import SchemaValidator
from ncad.spec.spec_loader import SpecLoader
from ncad.validate.semantic_validator import SemanticValidator

_BRIEFS_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "briefs"
_BRIEFS = sorted(_BRIEFS_DIR.glob("*.hocon"))


@pytest.mark.parametrize("brief_path", _BRIEFS, ids=lambda p: p.name)
def test_brief_compiles_to_valid_spec(brief_path: Path) -> None:
    brief = SpecLoader().load(str(brief_path))

    spec = SpecCompiler().compile(brief)

    assert SchemaValidator().validate(spec) == [], f"{brief_path.name} schema"
    assert SemanticValidator().validate(spec) == [], f"{brief_path.name} semantic"


def test_brief_fixtures_exist() -> None:
    assert _BRIEFS, "expected at least one brief fixture under tests/fixtures/briefs/"
