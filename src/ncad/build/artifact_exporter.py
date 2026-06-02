"""Export a spec's artifacts together: the 3D model and a BOM sidecar.

Writes ``<name>.glb`` (via the kernel) and ``<name>.bom.json`` (BOM computed from the
spec) into a directory. The sidecar lets the viewer show quantities without
re-deriving them from the mesh — the BOM stays spec-truth (design.md §4).
"""

import json
import logging
import os

from ncad.bom.bom_calculator import BomCalculator
from ncad.build.builder import Builder
from ncad.kernel.kernel import Kernel
from ncad.render.plan_renderer import PlanRenderer

logger = logging.getLogger(__name__)

_MODEL_EXTENSION = ".glb"
_BOM_SUFFIX = ".bom.json"
_PLAN_SUFFIX = ".plan.svg"


class ArtifactExporter:
    """Writes a model file and its BOM sidecar for a spec."""

    def __init__(self, kernel: Kernel) -> None:
        """:param kernel: Geometry backend used to build and export the model."""
        self._kernel = kernel
        self._bom_calculator = BomCalculator()
        self._plan_renderer = PlanRenderer()

    def export(self, spec: dict, directory: str, name: str) -> dict:
        """Build ``spec`` and write its model + BOM sidecar into ``directory``.

        :param spec: A schema-valid building spec dict.
        :param directory: Destination directory (created if absent).
        :param name: Base name for the output files (no extension).
        :return: Dict with ``"model"`` and ``"bom"`` absolute paths.
        """
        os.makedirs(directory, exist_ok=True)
        model_path = os.path.join(directory, name + _MODEL_EXTENSION)
        bom_path = os.path.join(directory, name + _BOM_SUFFIX)
        plan_path = os.path.join(directory, name + _PLAN_SUFFIX)

        solid = Builder(self._kernel).build(spec)
        self._kernel.export(solid, model_path)

        bom = self._bom_calculator.quantities(spec)
        with open(bom_path, "w", encoding="utf-8") as handle:
            json.dump(bom.as_dict(), handle, indent=2, sort_keys=True)

        self._plan_renderer.render_to_file(spec, plan_path)

        logger.info("exported %s, %s, %s", model_path, bom_path, plan_path)
        return {
            "model": os.path.abspath(model_path),
            "bom": os.path.abspath(bom_path),
            "plan": os.path.abspath(plan_path),
        }
