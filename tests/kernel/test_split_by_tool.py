import pytest

pytestmark = pytest.mark.slow


def test_split_by_tool_partitions_into_regions():
    from build123d import Pos, Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    block = Solid.make_box(20, 20, 20)
    tool = Pos(-5, -5, 6) * Solid.make_box(30, 30, 8)   # a slab crossing the block
    parts = kernel.split_by_tool(block, tool, keep="both")
    # Region inside the tool + region(s) outside; total volume equals the block.
    total = sum(sum(s.volume for s in p.solids()) for p in parts)
    assert abs(total - block.volume) < 1e-6
    assert len(parts) >= 2


def test_split_by_tool_keep_inside():
    from build123d import Pos, Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    block = Solid.make_box(20, 20, 20)
    tool = Pos(-5, -5, 6) * Solid.make_box(30, 30, 8)
    parts = kernel.split_by_tool(block, tool, keep="inside")
    assert len(parts) == 1
    assert abs(sum(s.volume for s in parts[0].solids()) - 3200.0) < 1e-6
