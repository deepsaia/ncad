"""SpecReference: resolve a cross-document reference relative to the referring document's dir.

``resolve(ref, base_dir)`` takes the referring doc's DIRECTORY; ``for_doc(ref, doc_path)`` dirnames
a file path first. Both return an absolute path (an absolute ref is returned as-is)."""

import os

from ncad.spec.spec_reference import SpecReference


def test_resolve_against_a_base_dir():
    ref = SpecReference()
    assert ref.resolve("crank.asm.hocon", "/proj/examples/07-motion") \
        == "/proj/examples/07-motion/crank.asm.hocon"


def test_resolve_parent_relative_reference():
    ref = SpecReference()
    assert ref.resolve("../parts/widget.hocon", "/proj/examples/asm") \
        == "/proj/examples/parts/widget.hocon"


def test_for_doc_resolves_against_the_referring_files_directory():
    # A .motion.hocon names its assembly; for_doc resolves it beside the motion doc.
    ref = SpecReference()
    assert ref.for_doc("crank.asm.hocon", "/proj/examples/07-motion/crank.motion.hocon") \
        == "/proj/examples/07-motion/crank.asm.hocon"


def test_absolute_reference_is_returned_as_is():
    ref = SpecReference()
    assert ref.resolve("/abs/lib/materials.hocon", "/proj/examples") == "/abs/lib/materials.hocon"
    assert ref.for_doc("/abs/lib/x.hocon", "/proj/examples/y.hocon") == "/abs/lib/x.hocon"


def test_relative_base_dir_is_normalized_to_absolute():
    # A relative base dir still yields an absolute path (matches the old os.path.join + abspath the
    # builders relied on).
    ref = SpecReference()
    assert ref.resolve("part.hocon", "examples/asm") == os.path.abspath("examples/asm/part.hocon")
