from ncad.docs.reference_exporter import ReferenceExporter
from ncad.ops.op_registry import OpRegistry


def test_export_covers_every_registered_op_exactly():
    export = ReferenceExporter().export()
    exported = {op["name"] for op in export["ops"]}
    registered = set(OpRegistry.with_defaults().op_names())
    assert exported == registered, f"drift: {exported ^ registered}"


def test_every_op_entry_has_a_name_and_example_list():
    export = ReferenceExporter().export()
    for op in export["ops"]:
        assert op["name"], "op has empty name"
        assert isinstance(op["examples"], list)  # may be empty (reference-only op)


def test_every_op_is_categorized_exactly_once():
    export = ReferenceExporter().export()
    # each op carries a category, and every op appears under exactly one category bucket.
    for op in export["ops"]:
        assert op["category"], f"{op['name']} has no category"
    listed = [name for cat in export["categories"] for name in cat["ops"]]
    assert sorted(listed) == sorted(op["name"] for op in export["ops"])
    assert len(listed) == len(set(listed)), "an op is listed in more than one category"


def test_examples_discovered_and_tagged_by_section_and_kind():
    export = ReferenceExporter().export()
    examples = export["examples"]
    assert examples, "no examples discovered"
    kinds = {e["kind"] for e in examples}
    assert kinds <= {"part", "assembly", "motion"}
    # A known kept example is present, tagged by its containing section dir.
    four_bar = next((e for e in examples if e["path"].endswith("07-motion/four_bar.hocon")), None)
    assert four_bar is not None
    assert four_bar["section"] == "07-motion"
    assert four_bar["kind"] == "part"
    assert "extrude" in four_bar["ops"] or "primitive" in four_bar["ops"]


def test_at_least_one_op_maps_to_a_real_example():
    export = ReferenceExporter().export()
    with_examples = [op for op in export["ops"] if op["examples"]]
    assert with_examples, "no op mapped to any example"
    # every example ref an op lists must be a real discovered example path
    all_paths = {e["path"] for e in export["examples"]}
    for op in with_examples:
        for ref in op["examples"]:
            assert ref in all_paths
