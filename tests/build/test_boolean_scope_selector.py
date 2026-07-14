import pytest

pytestmark = pytest.mark.slow


def test_boolean_scope_by_body_selector_query():
    # A keep-separate pattern makes a multibody part; a scope-mode boolean whose scope is a
    # 'select bodies where ...' query (by born-once id / created_by) fuses the matched bodies.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {
        "schema_version": 2, "units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 4, "h": 4}]},
            {"id": "blk", "op": "extrude", "profile": "sk", "distance": 4},
            {"id": "row", "op": "pattern", "kind": "linear",
             "x": {"dir": [1, 0, 0], "spacing": 10, "count": 3}, "merge": False},
            # Scope query: fuse the bodies created by the pattern (all 3).
            {"id": "fuse", "op": "boolean", "operation": "union",
             "scope": "select bodies where created_by = 'row'"},
        ]}},
    }
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    # The 3 disjoint pattern bodies, selected by the query, fuse to a single (multi-solid) body.
    assert len(kernel.bodies(result.shape)) == 1
