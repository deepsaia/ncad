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

from mkdocs.structure.files import File

from ncad.docs.reference_exporter import ReferenceExporter
from ncad.docs.reference_renderer import ReferenceRenderer

_EXPORT: dict = {}


def on_config(config):
    """Build the reference export once and splice categorized op pages into the nav."""
    export = ReferenceExporter().export()
    _EXPORT.clear()
    _EXPORT.update(export)

    # One nav subsection per category, each listing its op pages (skip empty categories).
    category_items = []
    for cat in export["categories"]:
        entries = [{op: f"ncad/reference/ops/{op}.md"} for op in cat["ops"]]
        if entries:
            category_items.append({cat["name"]: entries})

    ops_reference = {
        "Operations Reference": [
            {"Overview": "ncad/reference/index.md"},
            {"Capability Matrix": "ncad/reference/capability-matrix.md"},
            *category_items,
        ]
    }

    _replace_ops_reference(config.nav, ops_reference["Operations Reference"])
    return config


def on_files(files, config):
    """Inject the generated reference Markdown pages as virtual files (no disk writes)."""
    pages = ReferenceRenderer().render(_EXPORT)
    for src_uri, markdown in pages.items():
        files.append(File.generated(config, src_uri, content=markdown))
    return files


def _replace_ops_reference(nav, ops_children):
    """Find the placeholder 'Operations Reference' nav node and replace its children in place.

    mkdocs.yml declares an 'Operations Reference' entry (with just the overview + matrix); this
    swaps in the full, categorized op list generated from the registry.
    """
    for item in nav or []:
        if isinstance(item, dict):
            for key, value in item.items():
                if key == "Operations Reference" and isinstance(value, list):
                    item[key] = ops_children
                    return True
                if isinstance(value, list) and _replace_ops_reference(value, ops_children):
                    return True
    return False
