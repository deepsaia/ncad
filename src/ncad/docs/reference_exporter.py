"""Export the ncad reference data the documentation pages are generated from.

Single source of truth for the docs' ncad section: the authoritative op list (the op registry),
every shipped example discovered dynamically under ``examples/`` (so a newly added example appears
in the docs automatically, never a hardcoded list), and the mapping from each op to the examples
that actually exercise it. The Markdown generator (RenderMarkdown, a later task) consumes this;
keeping extraction here means the accuracy test can assert registry<->docs parity in one place.

No kernel and no geometry: this reads the registry + parses example documents only, so it is fast
and safe to run in CI. One class.
"""

import logging
import os

from ncad.ops.op_registry import OpRegistry
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_KIND_BY_TOP_KEY = {"parts": "part", "assembly": "assembly", "motion": "motion"}


class ReferenceExporter:
    """Collects the op list + the shipped examples + their op usage into one reference dict."""

    def __init__(self, examples_dir: str = "examples") -> None:
        self._examples_dir = examples_dir
        self._registry = OpRegistry.with_defaults()
        self._loader = SpecLoader()

    def export(self) -> dict:
        """Return ``{"ops": [...], "examples": [...]}``.

        ``ops`` has one entry per registered op: ``{name, examples}`` where ``examples`` is the
        list of discovered example paths that use the op. ``examples`` has one entry per shipped
        example: ``{path, section, kind, parts, ops}``.
        """
        examples = self._discover_examples()
        op_names = self._registry.op_names()
        ops = []
        for name in op_names:
            used_in = [e["path"] for e in examples if name in e["ops"]]
            ops.append({"name": name, "examples": used_in})
        return {"ops": ops, "examples": examples}

    def _discover_examples(self) -> list[dict]:
        """Walk ``examples/`` for .hocon documents; tag each by section dir, kind, parts, ops."""
        out: list[dict] = []
        for root, _dirs, files in os.walk(self._examples_dir):
            for fname in sorted(files):
                if not fname.endswith(".hocon"):
                    continue
                path = os.path.join(root, fname)
                record = self._describe_example(path)
                if record is not None:
                    out.append(record)
        out.sort(key=lambda e: e["path"])
        return out

    def _describe_example(self, path: str) -> dict | None:
        """Parse one example into ``{path, section, kind, parts, ops}`` (None if unreadable)."""
        try:
            document = self._loader.load(path)
        except (ValueError, OSError) as exc:
            logger.warning("docs exporter could not read %s: %s", path, exc)
            return None
        rel = os.path.relpath(path, self._examples_dir)
        section = rel.split(os.sep)[0] if os.sep in rel else ""
        kind = next((k for key, k in _KIND_BY_TOP_KEY.items() if key in document), "unknown")
        parts = sorted((document.get("parts") or {}).keys())
        ops = sorted(self._ops_used(document))
        return {"path": path, "section": section, "kind": kind, "parts": parts, "ops": ops}

    def _ops_used(self, document: dict) -> set[str]:
        """The set of op names appearing anywhere in a document's feature trees (recursive)."""
        found: set[str] = set()
        self._collect_ops(document, found)
        return found

    def _collect_ops(self, node: object, found: set[str]) -> None:
        """Recurse any dict/list, recording every ``op`` field value (a feature's builder name)."""
        if isinstance(node, dict):
            op = node.get("op")
            if isinstance(op, str):
                found.add(op)
            for value in node.values():
                self._collect_ops(value, found)
        elif isinstance(node, list):
            for item in node:
                self._collect_ops(item, found)
