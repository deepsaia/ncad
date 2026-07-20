"""Render the Learn taxonomy into Markdown pages for the MkDocs site.

Pure function of the taxonomy dict (docs/documentation-structure.json): produces
``{relative_md_path: markdown}`` for every subject/topic/subtopic index and every concept page.
A concept page carries its summary, its display math (KaTeX via arithmatex), its authored body if
present (else an honest "authoring in progress" stub, never fabricated content), an "In ncad"
status admonition drawn from the node's ncad block, a Sources list, and a 3D model-viewer embed
when the node names a demo model. The MkDocs hook writes these into the virtual tree at build time.

One class; no filesystem writes (that is the hook's job), which keeps it unit-testable. Section
pages are placed at ``learn/<path>/index.md`` and concepts at ``learn/<path>/<slug>.md`` so the
URL structure mirrors the taxonomy.
"""

import logging
import os

logger = logging.getLogger(__name__)

_LEARN_ROOT = "learn"
_CHILD_KEYS = ("topics", "subtopics", "concepts", "children")
_STATUS_ADMONITION = {
    "available": "success",
    "partial": "info",
    "wip": "warning",
    "planned": "note",
    "not-in-scope": "quote",
}
_STATUS_LABEL = {
    "available": "Available",
    "partial": "Partial",
    "wip": "WIP",
    "planned": "Planned",
    "not-in-scope": "Not-in-scope",
}


class LearnRenderer:
    """Turns the Learn taxonomy into Markdown pages (section indexes + concept pages).

    Concept bodies may be inline (``body``) or in an adjacent Markdown file (``body_file``,
    resolved relative to ``content_dir``); the file form keeps long professional prose out of the
    JSON. A concept with neither renders an honest "authoring in progress" stub.
    """

    def __init__(self, content_dir: str = "docs_site/learn_content") -> None:
        self._content_dir = content_dir

    def render(self, taxonomy: dict) -> dict[str, str]:
        """Return ``{path: markdown}`` for every Learn section index + concept page."""
        pages: dict[str, str] = {}
        for subject in taxonomy.get("subjects", []):
            self._walk(subject, [subject.get("slug") or _slug(subject["id"])], pages)
        return pages

    def _walk(self, node: dict, path: list[str], pages: dict[str, str]) -> None:
        """Recurse the taxonomy, emitting an index page per section and a page per concept."""
        children = self._children(node)
        if node.get("level") == "concept":
            key = f"{_LEARN_ROOT}/{'/'.join(path[:-1])}/{path[-1]}.md"
            pages[key] = self._concept_page(node)
            return
        # section node (subject/topic/subtopic): an index page listing its children.
        pages[f"{_LEARN_ROOT}/{'/'.join(path)}/index.md"] = self._section_page(node, children)
        for child in children:
            slug = child.get("slug") or _slug(child["id"])
            self._walk(child, [*path, slug], pages)

    def _children(self, node: dict) -> list[dict]:
        for k in _CHILD_KEYS:
            if isinstance(node.get(k), list):
                return node[k]
        return []

    def _section_page(self, node: dict, children: list[dict]) -> str:
        """A subject/topic/subtopic landing page: title, summary, and links to its children."""
        lines = [f"# {node['title']}", ""]
        if node.get("summary"):
            lines += [node["summary"], ""]
        for child in children:
            slug = child.get("slug") or _slug(child["id"])
            target = f"{slug}.md" if child.get("level") == "concept" else f"{slug}/index.md"
            summary = child.get("summary")
            suffix = f" - {summary}" if summary else ""
            lines.append(f"- [{child['title']}]({target}){suffix}")
        lines.append("")
        return "\n".join(lines)

    def _concept_page(self, node: dict) -> str:
        """A concept page: teaching body (or honest stub) + math + In-ncad box + sources + 3D."""
        lines = [f"# {node['title']}", ""]
        if node.get("summary"):
            lines += [f"*{node['summary']}*", ""]
        lines += self._math_block(node.get("math") or [])
        lines += self._body_block(node)
        lines += self._model_block(node)
        lines += self._ncad_block(node.get("ncad"))
        lines += self._sources_block(node.get("sources") or [])
        return "\n".join(lines)

    def _math_block(self, math: list[dict]) -> list[str]:
        """Render each math entry as a KaTeX display block (arithmatex ``\\[ ... \\]``)."""
        out: list[str] = []
        for entry in math:
            tex = entry.get("tex")
            if not tex:
                continue
            out += ["\\[", tex, "\\]", ""]
            if entry.get("caption"):
                out += [f"*{entry['caption']}*", ""]
        return out

    def _body_block(self, node: dict) -> list[str]:
        """The authored teaching body, or an honest 'authoring in progress' stub if absent.

        Prefers an inline ``body``; else loads ``body_file`` (relative to content_dir); else stub.
        """
        body = node.get("body")
        if not (isinstance(body, str) and body.strip()):
            body = self._load_body_file(node.get("body_file"))
        if isinstance(body, str) and body.strip():
            return [body.strip(), ""]
        return [
            "!!! note \"Authoring in progress\"",
            "    This concept is part of the reference taxonomy but its full write-up is not yet "
            "authored. The status box below reflects ncad's current support.",
            "",
        ]

    def _load_body_file(self, body_file: str | None) -> str | None:
        """Read a concept's adjacent Markdown body (relative to content_dir); None if absent."""
        if not body_file:
            return None
        path = os.path.join(self._content_dir, body_file)
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read()
        except OSError as exc:
            logger.warning("learn renderer could not read body file %s: %s", path, exc)
            return None

    def _model_block(self, node: dict) -> list[str]:
        """A 3D <model-viewer> embed when the node names a demo glTF/GLB (via a `model` field)."""
        model = node.get("model")
        if not model:
            return []
        return [
            f'<model-viewer src="{model}" camera-controls auto-rotate '
            'style="width:100%;height:420px" alt="3D model"></model-viewer>',
            "",
        ]

    def _ncad_block(self, ncad: dict | None) -> list[str]:
        """The 'In ncad' status admonition, drawn from the node's ncad object."""
        if not ncad or not ncad.get("status"):
            return []
        status = ncad["status"]
        adm = _STATUS_ADMONITION.get(status, "note")
        label = _STATUS_LABEL.get(status, status)
        out = [f'!!! {adm} "In ncad: {label}"']
        if ncad.get("notes"):
            out.append(f"    {ncad['notes']}")
        if ncad.get("engine"):
            out.append("")
            out.append(f"    Delegated engine: **{ncad['engine']}**.")
        for ref in ncad.get("refs") or []:
            out.append("")
            out.append(f"    See: [{ref}]({ref})")
        out.append("")
        return out

    def _sources_block(self, sources: list[dict]) -> list[str]:
        """A Sources list of tiered, typed citations."""
        if not sources:
            return []
        out = ["## Sources", ""]
        for s in sources:
            bits = [f"**{s.get('title', '(untitled)')}**"]
            if s.get("authors"):
                bits.append(s["authors"])
            if s.get("year"):
                bits.append(str(s["year"]))
            if s.get("edition"):
                bits.append(s["edition"])
            if s.get("locator"):
                bits.append(s["locator"])
            text = ", ".join(bits)
            tier = s.get("tier", "")
            typ = s.get("type", "")
            tag = f" _({tier} {typ})_".rstrip()
            url = s.get("url")
            line = f"- [{text}]({url}){tag}" if url else f"- {text}{tag}"
            out.append(line)
        out.append("")
        return out


def _slug(dotted_id: str) -> str:
    """The last dotted segment of a node id, used as its URL slug when no explicit slug is set."""
    return dotted_id.rsplit(".", 1)[-1]
