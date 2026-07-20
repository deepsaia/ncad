"""The docs honesty gate: the generated documentation can never claim what the code cannot do.

Three properties, all tested against the live code (not a snapshot):
  1. Registry <-> reference parity: every registered op has exactly one generated op page, and every
     generated op page names a real registered op.
  2. Examples validate: every example the reference embeds/links still passes DocumentValidator, so
     a shown snippet is never one that no longer builds.
  3. Taxonomy shape: every Learn node validates against the content-node JSON schema, and any
     concept that carries an ncad=available/partial claim is shape-consistent.

A renamed op, a deleted example, or a malformed taxonomy node fails this gate.
"""

import json
import os

import jsonschema

from ncad.diagnostics.document_validator import DocumentValidator
from ncad.docs.reference_exporter import ReferenceExporter
from ncad.docs.reference_renderer import ReferenceRenderer
from ncad.ops.op_registry import OpRegistry

_SCHEMA_PATH = "docs_site/schema/content-node.schema.json"
_TAXONOMY_PATH = "docs/documentation-structure.json"
_CHILD_KEYS = ("topics", "subtopics", "concepts", "children")


def _iter_nodes(node):
    yield node
    for key in _CHILD_KEYS:
        for child in node.get(key, []) or []:
            yield from _iter_nodes(child)


def test_registry_and_reference_pages_are_in_parity():
    export = ReferenceExporter().export()
    pages = ReferenceRenderer().render(export)
    registered = set(OpRegistry.with_defaults().op_names())
    page_ops = {
        path.rsplit("/", 1)[-1][:-3]
        for path in pages
        if path.startswith("ncad/reference/ops/") and path.endswith(".md")
    }
    assert page_ops == registered, f"op-page drift: {page_ops ^ registered}"


def test_every_referenced_example_still_validates():
    export = ReferenceExporter().export()
    referenced = {p for op in export["ops"] for p in op["examples"]}
    assert referenced, "no examples referenced by any op"
    for path in sorted(referenced):
        report = DocumentValidator(base_dir=os.path.dirname(path)).validate(_load_resolved(path))
        errors = [d for d in report.diagnostics if d.severity == "error"]
        assert not errors, f"referenced example {path} no longer validates: {errors}"


def test_every_taxonomy_node_is_shape_valid():
    schema = json.load(open(_SCHEMA_PATH))
    taxonomy = json.load(open(_TAXONOMY_PATH))
    validator = jsonschema.Draft202012Validator(schema)
    bad = []
    for subject in taxonomy["subjects"]:
        for node in _iter_nodes(subject):
            errors = list(validator.iter_errors(node))
            if errors:
                bad.append((node.get("id", "?"), errors[0].message))
    assert not bad, f"malformed taxonomy nodes: {bad[:5]}"


def test_authored_concepts_have_a_primary_source():
    """A concept with an authored body (body or body_file) must cite at least one primary source,
    the professional-depth bar. Un-authored stubs are exempt (they are honestly incomplete)."""
    taxonomy = json.load(open(_TAXONOMY_PATH))
    offenders = []
    for subject in taxonomy["subjects"]:
        for node in _iter_nodes(subject):
            if node.get("level") != "concept":
                continue
            authored = node.get("body") or node.get("body_file")
            if not authored:
                continue
            sources = node.get("sources") or []
            if not any(s.get("tier") == "primary" for s in sources):
                offenders.append(node["id"])
    assert not offenders, f"authored concepts missing a primary source: {offenders}"


def _load_resolved(path):
    """Load an example and resolve parameter expressions before validating, matching the build +
    ``ncad validate`` path (a "${t}" field becomes a number before schema checks)."""
    from ncad.params.function_registry import FunctionRegistry
    from ncad.params.param_resolver import ParamResolver
    from ncad.spec.spec_loader import SpecLoader

    document = SpecLoader().load(path)
    return ParamResolver(FunctionRegistry.with_defaults()).resolve_document(document)
