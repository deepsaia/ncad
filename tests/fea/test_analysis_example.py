import os

import pytest

from ncad.diagnostics.document_validator import DocumentValidator
from ncad.fea.analysis_spec import AnalysisSpec
from ncad.spec.spec_loader import SpecLoader

_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "examples", "10-fea")
_EXAMPLE = os.path.join(_DIR, "bracket.analysis.hocon")
# The load cases shipped under examples/10-fea (each references a part .hocon in the same dir).
_ANALYSES = ["bracket.analysis.hocon", "f1_front_wing.analysis.hocon", "con_rod.analysis.hocon"]


def test_bracket_analysis_example_parses():
    spec = AnalysisSpec(SpecLoader().load(_EXAMPLE))
    assert spec.part
    assert spec.steps and spec.constraints


def test_bracket_analysis_example_validates_ok():
    doc = SpecLoader().load(_EXAMPLE)
    report = DocumentValidator(base_dir=os.path.dirname(os.path.abspath(_EXAMPLE))).validate(doc)
    assert report.ok is True


@pytest.mark.parametrize("name", _ANALYSES)
def test_shipped_analysis_examples_parse(name):
    spec = AnalysisSpec(SpecLoader().load(os.path.join(_DIR, name)))
    assert spec.part and spec.steps and spec.constraints and spec.loads


@pytest.mark.parametrize("name", _ANALYSES)
def test_shipped_analysis_examples_validate_ok(name):
    path = os.path.join(_DIR, name)
    doc = SpecLoader().load(path)
    report = DocumentValidator(base_dir=os.path.dirname(os.path.abspath(path))).validate(doc)
    assert report.ok is True
