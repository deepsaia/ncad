"""Fixture specs must load and pass schema validation.

This ties loader + schema + fixtures together as a regression net: if any drifts, this
breaks. New fixtures added to tests/fixtures/ are picked up automatically.
"""

from pathlib import Path

import pytest

from ncad.spec.schema_validator import SchemaValidator
from ncad.spec.spec_loader import SpecLoader

_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
_FIXTURE_SPECS = sorted(
    p for p in _FIXTURES_DIR.glob("*") if p.suffix.lower() in (".hocon", ".conf", ".json")
)


@pytest.mark.parametrize("spec_path", _FIXTURE_SPECS, ids=lambda p: p.name)
def test_fixture_spec_is_schema_valid(spec_path: Path) -> None:
    spec = SpecLoader().load(str(spec_path))

    issues = SchemaValidator().validate(spec)

    assert issues == [], f"{spec_path.name} has schema issues: {issues}"


def test_box_house_fixture_exists() -> None:
    assert (_FIXTURES_DIR / "box_house.hocon") in _FIXTURE_SPECS
