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

# Op categories, in the order they should appear in the docs (grouped the way CAD tools group
# their operation menus). Every registered op must map to exactly one category; the exporter
# asserts full coverage so a newly added op cannot silently fall out of the reference nav.
_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Sketching", ["sketch"]),
    ("Primitives", ["primitive"]),
    ("Sketched features",
     ["extrude", "pocket", "revolve", "groove", "sweep", "path3d", "loft", "rib"]),
    ("Dress-up", ["fillet", "chamfer", "shell", "draft", "hole", "thread", "wrap"]),
    ("Patterns & transforms",
     ["pattern", "mirror", "transform", "feature_pattern", "feature_mirror"]),
    ("Booleans & multibody", ["boolean", "split"]),
    ("Direct / synchronous", ["defeature", "offset", "move_face", "relate", "reposition_hole"]),
    ("Datums", ["datum_plane", "datum_axis"]),
    ("Import", ["import"]),
]


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
        category_of = self._category_map(op_names)
        ops = []
        for name in op_names:
            used_in = [e["path"] for e in examples if name in e["ops"]]
            ops.append({"name": name, "summary": self._op_summary(name),
                        "category": category_of[name], "examples": used_in})
        categories = [{"name": cat, "ops": [n for n in names if n in op_names]}
                      for cat, names in _CATEGORIES]
        return {"ops": ops, "categories": categories, "examples": examples}

    def _category_map(self, op_names: list[str]) -> dict[str, str]:
        """Map each op to its category, asserting every registered op is categorized exactly once.

        A missing op (a new op added to the registry without a category here) raises, so the
        reference nav can never silently drop an operation.
        """
        mapping: dict[str, str] = {}
        for cat, names in _CATEGORIES:
            for name in names:
                mapping[name] = cat
        uncategorized = [n for n in op_names if n not in mapping]
        if uncategorized:
            raise ValueError(
                f"ops missing a docs category (add them to _CATEGORIES): {sorted(uncategorized)}")
        return mapping

    def _op_summary(self, name: str) -> str:
        """The op's one-line description: the first line of its Op class docstring (real, not made
        up). Empty string if the class has no docstring."""
        builder = self._registry.get(name)
        op_class = getattr(builder, "__self__", None)
        doc = (type(op_class).__doc__ or "").strip() if op_class is not None else ""
        return doc.split("\n", 1)[0].strip() if doc else ""

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
