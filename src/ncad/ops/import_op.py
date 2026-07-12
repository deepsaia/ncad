"""The ``import`` leaf op: turn a STEP/IGES file into the base feature of a document.

An imported solid has no construction history, so the naming layer seeds its element names
geometrically (OpResult.history stays None). Direct-edit features (Phase 4.2) append on top.
"""

import logging
from typing import Any

from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult

logger = logging.getLogger(__name__)


class ImportOp:
    """Imports a STEP/IGES solid as a document's base feature."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict,
              kernel: Any) -> OpResult:
        """Import a solid from ``params['file']`` (ignores ``shape_in``: this is a leaf op)."""
        node_id = params.get("id", "import")
        path = params.get("file")
        if not path:
            return OpResult(shape=None, issues=[BuildIssue(
                node_id=node_id, message="import requires a 'file' path")])
        try:
            shape = kernel.import_solid(path)
        except (OSError, ValueError, RuntimeError) as exc:
            logger.warning("import failed for %s: %s", path, exc)
            return OpResult(shape=None, issues=[BuildIssue(
                node_id=node_id, message=f"could not import {path!r}: {exc}")])
        # Validate-on-load: a non-solid / empty import must not become a silent bad base feature.
        if shape is None or kernel.volume(shape) <= 0.0:
            return OpResult(shape=None, issues=[BuildIssue(
                node_id=node_id, message=f"import {path!r} is not a valid solid")])
        # history stays None: no lineage, so names seed from geometry (design section 6).
        return OpResult(shape=shape)
