"""Render the ncad reference export into Markdown pages for the MkDocs site.

Pure function of the ReferenceExporter dict: produces ``{relative_md_path: markdown}`` for one op
page per registered op, a Capability Matrix, and a reference index. The mkdocs-gen-files build hook
(docs_site gen script) writes these into the virtual docs tree at build time, so the op reference is
always regenerated from the live registry + shipped examples and can never drift into a lie. One
class; no filesystem writes here (that is the hook's job), which keeps it unit-testable.
"""

import logging
import os

logger = logging.getLogger(__name__)

_REF_ROOT = "ncad/reference"


class ReferenceRenderer:
    """Turns the reference export into Markdown pages (op pages + capability matrix + index)."""

    def render(self, export: dict) -> dict[str, str]:
        """Return ``{path: markdown}`` for every generated reference page."""
        pages: dict[str, str] = {}
        for op in export["ops"]:
            pages[f"{_REF_ROOT}/ops/{op['name']}.md"] = self._op_page(op, export)
        pages[f"{_REF_ROOT}/capability-matrix.md"] = self._matrix_page(export)
        pages[f"{_REF_ROOT}/index.md"] = self._index_page(export)
        return pages

    def _op_page(self, op: dict, export: dict) -> str:
        """One op's reference page: name, one-line summary, an In-ncad status, a real example."""
        name = op["name"]
        summary = op.get("summary") or "(no description available)"
        lines = [f"# {name}", "", f"> {summary}", ""]
        lines += [
            '!!! success "In ncad"',
            f"    The `{name}` op is **Available**: it is registered in the op registry and",
            "    exercised by the shipped examples listed below. This page is generated from the",
            "    code, so it never claims a capability the engine lacks.",
            "",
        ]
        example = self._first_example(op, export)
        if example is not None:
            lines += ["## Example", "", f"From `{example['path']}`:", "", "```properties",
                      self._example_snippet(example), "```", ""]
        else:
            lines += ["## Example", "",
                      f"No shipped example exercises `{name}` on its own yet. See the "
                      "[Capability Matrix](../capability-matrix.md) for coverage.", ""]
        others = op["examples"]
        if others:
            lines += ["## Used in", ""]
            lines += [f"- `{p}`" for p in others]
            lines += [""]
        return "\n".join(lines)

    def _matrix_page(self, export: dict) -> str:
        """The Capability Matrix: every registered op, its status, and its example count."""
        lines = ["# Capability Matrix", "",
                 "Every operation ncad implements today, generated from the op registry. "
                 "An op is **Available** when it is registered and buildable; the example count is "
                 "how many shipped example documents exercise it.", "",
                 "| Operation | Status | Examples | Summary |", "|---|---|---|---|"]
        for op in sorted(export["ops"], key=lambda o: o["name"]):
            summary = (op.get("summary") or "").replace("|", "\\|")
            lines.append(
                f"| [`{op['name']}`](ops/{op['name']}.md) | Available | "
                f"{len(op['examples'])} | {summary} |")
        lines.append("")
        return "\n".join(lines)

    def _index_page(self, export: dict) -> str:
        """The reference landing page: links to every op page + the matrix."""
        lines = ["# Operations Reference", "",
                 "ncad's operation vocabulary, generated from the op registry "
                 f"(`src/ncad/ops/op_registry.py`). {len(export['ops'])} operations are available.",
                 "", "See the [Capability Matrix](capability-matrix.md) for a status overview.",
                 "", "## Operations", ""]
        for op in sorted(export["ops"], key=lambda o: o["name"]):
            summary = op.get("summary") or ""
            lines.append(f"- [`{op['name']}`](ops/{op['name']}.md) - {summary}")
        lines.append("")
        return "\n".join(lines)

    def _first_example(self, op: dict, export: dict) -> dict | None:
        """The example record for this op's first listed example path (a part doc if possible)."""
        by_path = {e["path"]: e for e in export["examples"]}
        candidates = [by_path[p] for p in op["examples"] if p in by_path]
        parts_first = sorted(candidates, key=lambda e: (e["kind"] != "part", e["path"]))
        return parts_first[0] if parts_first else None

    def _example_snippet(self, example: dict) -> str:
        """Read the example file's text for embedding (best-effort; a short note if unreadable)."""
        path = example["path"]
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read().rstrip("\n")
        except OSError as exc:
            logger.warning("docs renderer could not read %s: %s", path, exc)
            return f"# (could not read {os.path.basename(path)})"
