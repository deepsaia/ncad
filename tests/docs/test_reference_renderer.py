from ncad.docs.reference_exporter import ReferenceExporter
from ncad.docs.reference_renderer import ReferenceRenderer


def test_renders_one_page_per_op():
    export = ReferenceExporter().export()
    pages = ReferenceRenderer().render(export)
    for op in export["ops"]:
        key = f"ncad/reference/ops/{op['name']}.md"
        assert key in pages, f"missing op page {key}"
        assert pages[key].startswith(f"# {op['name']}")


def test_op_page_embeds_a_real_example_when_one_exists():
    export = ReferenceExporter().export()
    pages = ReferenceRenderer().render(export)
    # extrude is exercised by shipped examples; its page must show a fenced code block.
    extrude = pages["ncad/reference/ops/extrude.md"]
    assert "```" in extrude
    assert "op = extrude" in extrude or "op=extrude" in extrude


def test_capability_matrix_lists_every_op():
    export = ReferenceExporter().export()
    pages = ReferenceRenderer().render(export)
    matrix = pages["ncad/reference/capability-matrix.md"]
    for op in export["ops"]:
        assert op["name"] in matrix


def test_reference_index_links_all_ops():
    export = ReferenceExporter().export()
    pages = ReferenceRenderer().render(export)
    index = pages["ncad/reference/index.md"]
    for op in export["ops"]:
        assert f"ops/{op['name']}.md" in index
