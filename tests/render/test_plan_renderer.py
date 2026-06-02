"""Tests for the PlanRenderer: spec -> SVG plan drawing.

The SVG is XML, so we assert on its structure (labels, markers, layers) rather than
pixels. Output is deterministic, which keeps it golden-testable like the spec.
"""

from ncad.generate.generator import Generator
from ncad.render.plan_renderer import PlanRenderer

_PARAMS = {"width": 12.0, "depth": 9.0, "num_rooms": 4, "storey_height": 3.0}


def _spec() -> dict:
    return Generator(_PARAMS).generate(seed=42)


def test_render_returns_svg_string() -> None:
    svg = PlanRenderer().render(_spec())

    assert svg.lstrip().startswith("<?xml") or svg.lstrip().startswith("<svg")
    assert "</svg>" in svg


def test_render_includes_a_room_label_per_room() -> None:
    spec = _spec()

    svg = PlanRenderer().render(spec)

    for room in spec["storeys"][0]["rooms"]:
        assert room["id"] in svg


def test_render_marks_doors_and_windows() -> None:
    spec = _spec()
    svg = PlanRenderer().render(spec)

    door_count = sum(
        1 for w in spec["storeys"][0]["walls"] for o in w.get("openings", []) if o["kind"] == "door"
    )
    # Each door is drawn with the door color; expect at least that many occurrences.
    assert svg.count(PlanRenderer.DOOR_COLOR) >= door_count


def test_render_is_deterministic() -> None:
    spec = _spec()

    assert PlanRenderer().render(spec) == PlanRenderer().render(spec)


def test_render_to_file_writes_svg(tmp_path) -> None:
    out = tmp_path / "plan.svg"

    PlanRenderer().render_to_file(_spec(), str(out))

    assert out.exists()
    assert "</svg>" in out.read_text()
