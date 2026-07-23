import os

from ncad.diagnostics.document_validator import DocumentValidator
from ncad.fea.analysis_spec import AnalysisSpec
from ncad.spec.spec_loader import SpecLoader

_EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "..",
                        "examples", "10-fea", "bracket.analysis.hocon")


def test_bracket_analysis_example_parses():
    spec = AnalysisSpec(SpecLoader().load(_EXAMPLE))
    assert spec.part
    assert spec.steps and spec.constraints


def test_bracket_analysis_example_validates_ok():
    doc = SpecLoader().load(_EXAMPLE)
    report = DocumentValidator(base_dir=os.path.dirname(os.path.abspath(_EXAMPLE))).validate(doc)
    assert report.ok is True
