"""MkDocs core hooks: generate the ncad Operations Reference at build time.

Uses MkDocs' built-in hook mechanism (no plugin, so no advertising-injecting transitive
dependency). Two hooks:

- on_config: splice the generated op pages into ``config.nav`` (grouped by category) BEFORE the
  nav is built, so MkDocs builds one native, fully-linked navigation tree. Injecting here (not in
  on_nav) is what keeps the left sidebar present + complete on every op page.
- on_files: inject each rendered page as a generated File (nothing is written into the repo).

This keeps the reference in lockstep with the code, the docs never claim a capability the engine
lacks, and every op appears in the sidebar under its category.
"""

import json
import os

from mkdocs.structure.files import File

from ncad.docs.learn_renderer import LearnRenderer
from ncad.docs.reference_exporter import ReferenceExporter
from ncad.docs.reference_renderer import ReferenceRenderer

_TAXONOMY_PATH = os.path.join("docs", "documentation-structure.json")

_EXPORT: dict = {}
_TAXONOMY: dict = {}


def on_config(config):
    """Build the reference export + load the taxonomy, then splice both into the nav."""
    export = ReferenceExporter().export()
    _EXPORT.clear()
    _EXPORT.update(export)
    with open(_TAXONOMY_PATH, encoding="utf-8") as handle:
        taxonomy = json.load(handle)
    _TAXONOMY.clear()
    _TAXONOMY.update(taxonomy)

    # ncad > Operations Reference: one nav subsection per category (skip empty categories).
    category_items = []
    for cat in export["categories"]:
        entries = [{op: f"ncad/reference/ops/{op}.md"} for op in cat["ops"]]
        if entries:
            category_items.append({cat["name"]: entries})
    ops_reference_children = [
        {"Overview": "ncad/reference/index.md"},
        {"Capability Matrix": "ncad/reference/capability-matrix.md"},
        *category_items,
    ]
    _replace_named_section(config.nav, "Operations Reference", ops_reference_children)

    # Learn > (one entry per subject, mirroring the taxonomy tree).
    learn_children = [_learn_nav(subject) for subject in taxonomy.get("subjects", [])]
    _replace_named_section(config.nav, "Learn", learn_children)
    return config


def on_files(files, config):
    """Inject the generated reference + Learn Markdown pages as virtual files (no disk writes)."""
    pages = ReferenceRenderer().render(_EXPORT)
    pages.update(LearnRenderer().render(_TAXONOMY))
    for src_uri, markdown in pages.items():
        files.append(File.generated(config, src_uri, content=markdown))
    return files


_CHILD_KEYS = ("topics", "subtopics", "concepts", "children")
_LEARN_ROOT = "learn"


def _learn_nav(node, path=None):
    """A nav entry for one taxonomy node, mirroring LearnRenderer's page paths.

    A concept maps to its single page; a section maps to ``{title: [index, ...children]}`` so the
    section's own index plus every child appears in the left sidebar tree.
    """
    slug = node.get("slug") or node["id"].rsplit(".", 1)[-1]
    path = [*(path or []), slug]
    children = _taxonomy_children(node)
    if node.get("level") == "concept" or not children:
        page = f"{_LEARN_ROOT}/{'/'.join(path)}.md"
        return {node["title"]: page}
    entries = [{"Overview": f"{_LEARN_ROOT}/{'/'.join(path)}/index.md"}]
    entries += [_learn_nav(child, path) for child in children]
    return {node["title"]: entries}


def _taxonomy_children(node):
    for k in _CHILD_KEYS:
        if isinstance(node.get(k), list):
            return node[k]
    return []


def _replace_named_section(nav, title, children):
    """Find the placeholder nav node named ``title`` and replace its children in place.

    mkdocs.yml declares a minimal placeholder (e.g. 'Learn', 'Operations Reference'); this swaps in
    the full tree generated from the taxonomy / op registry at build time.
    """
    for item in nav or []:
        if isinstance(item, dict):
            for key, value in item.items():
                if key == title and isinstance(value, list):
                    item[key] = children
                    return True
                if isinstance(value, list) and _replace_named_section(value, title, children):
                    return True
    return False
