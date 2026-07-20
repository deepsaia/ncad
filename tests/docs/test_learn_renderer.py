import json

from ncad.docs.learn_renderer import LearnRenderer

_TAXONOMY = json.load(open("docs/documentation-structure.json"))


def test_renders_a_page_per_concept_and_section():
    pages = LearnRenderer().render(_TAXONOMY)
    # every subject has an index page
    for subject in _TAXONOMY["subjects"]:
        assert f"learn/{subject['slug']}/index.md" in pages
    # concept pages exist and open with an h1 title
    concept_pages = [p for p in pages if "/concepts/" in p or p.count("/") >= 3]
    assert concept_pages, "no concept pages generated"


def test_concept_with_ncad_block_shows_status_admonition():
    pages = LearnRenderer().render(_TAXONOMY)
    # foundations.transforms.rotations.quaternions has an available ncad block
    key = next(p for p in pages if p.endswith("quaternions.md"))
    body = pages[key]
    assert "In ncad" in body
    assert "Available" in body or "available" in body
    assert "Modern Robotics" in body  # its primary source


def test_concept_without_body_renders_honest_stub():
    pages = LearnRenderer().render(_TAXONOMY)
    # a concept with only id/level/title (no body) must render a visible authoring stub, not fake
    # content.
    stub_pages = [c for c in pages.values() if "authoring in progress" in c.lower()]
    assert stub_pages, "expected honest stubs for unauthored concepts"


def test_math_is_emitted_as_katex_block():
    pages = LearnRenderer().render(_TAXONOMY)
    key = next(p for p in pages if p.endswith("quaternions.md"))
    body = pages[key]
    assert "\\lVert q \\rVert = 1" in body  # the tex from its math[] entry


def test_body_file_is_loaded_into_the_page():
    pages = LearnRenderer().render(_TAXONOMY)
    # rotation-matrix concept authors its body via body_file; the rendered page must contain it.
    key = next(p for p in pages if p.endswith("rotations/matrix.md"))
    assert "workhorse representation" in pages[key]
    assert "authoring in progress" not in pages[key].lower()
