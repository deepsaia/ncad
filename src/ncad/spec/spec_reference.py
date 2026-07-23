"""Resolve a cross-document reference in a spec to an absolute path.

ncad specs point at OTHER documents that are built independently: a motion doc names the
``assembly`` it drives, an assembly instance names the part ``file`` it places, a sub-assembly
names a child ``.asm.hocon``, a physics overlay names its ``assembly``, a part may name an external
``materials_library``. These are NOT HOCON ``include``/``${}`` (which inline one config): the target
is loaded and BUILT as its own document, so the reference is a semantic pointer, not a text merge.

Every such reference resolves the same way - relative to the directory of the document that NAMES
it (an absolute reference is taken as-is), the leaf-common convention. That one rule was inlined
across the builders; this centralises it so the convention lives in one place. One class.
"""

import os


class SpecReference:
    """Resolves a document-relative spec reference to an absolute filesystem path."""

    def resolve(self, reference: str, base_dir: str) -> str:
        """Return the absolute path for ``reference`` resolved against ``base_dir``.

        :param reference: The reference string as authored in the spec (e.g. ``"crank.asm.hocon"``
            or ``"../parts/widget.hocon"``); an absolute path is returned unchanged.
        :param base_dir: The referring document's DIRECTORY (the leaf-common relative convention).
            A file-path caller passes ``os.path.dirname(doc_path)``; use ``for_doc`` to do that.
        :return: The absolute path of the referenced document (not checked for existence here).
        """
        if os.path.isabs(reference):
            return os.path.abspath(reference)
        return os.path.abspath(os.path.join(base_dir, reference))

    def for_doc(self, reference: str, referring_doc: str) -> str:
        """Resolve ``reference`` against the DIRECTORY of the file ``referring_doc`` names it in."""
        return self.resolve(reference, os.path.dirname(referring_doc))
