"""Build a motion study document (.motion.hocon): drive a referenced assembly and emit a trajectory.

A motion document is a first-class kind (like part / assembly, design section 8): it names the
assembly it drives plus a driver, and produces the assembly scene sidecar AND the .motion.json
trajectory. One assembly can back several motion studies (different drivers / speeds / ranges). This
builder resolves the referenced assembly path (relative to the motion doc), then delegates to
AssemblyBuilder.assemble with the motion spec injected, so the whole solve/export path is reused.
"""

import logging
import os
from typing import Any

from ncad.assembly.assembly_builder import AssemblyBuilder
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)


class MotionBuilder:
    """Loads a .motion.hocon, resolves its assembly, and runs the driven-motion build."""

    def __init__(self, kernel: Any) -> None:
        self._loader = SpecLoader()
        self._assembler = AssemblyBuilder(kernel)

    def build(self, motion_path: str, out_dir: str) -> dict:
        """Build the motion study at ``motion_path`` into ``out_dir``; return the assembly result.

        The result dict is the AssemblyBuilder result ({sidecar, issues, motion, instances}); the
        ``motion`` key is the trajectory sidecar path. Raises ValueError on a malformed motion doc.
        """
        document = self._loader.load(motion_path)
        motion = document.get("motion")
        if not isinstance(motion, dict):
            raise ValueError("a motion document needs a top-level 'motion' block")
        assembly_ref = motion.get("assembly")
        if not isinstance(assembly_ref, str) or not assembly_ref:
            raise ValueError("a motion document's 'motion' block needs an 'assembly' reference")
        motion_dir = os.path.dirname(os.path.abspath(motion_path))
        assembly_path = os.path.join(motion_dir, assembly_ref)
        if not os.path.isfile(assembly_path):
            raise ValueError(f"motion references a missing assembly: {assembly_ref!r}")
        # The motion spec passed to the assembler is the driver block plus the optional `outputs`
        # block (traces + measures, bucket 6.1); the assembly reference has done its job of locating
        # the mechanism. The trajectory sidecar is named after the ASSEMBLY (so the viewer finds
        # <assembly>.motion.json beside <assembly>.assembly.json).
        motion_spec = {"driver": motion.get("driver"), "outputs": motion.get("outputs")}
        result = self._assembler.assemble(assembly_path, out_dir, motion_spec=motion_spec)
        logger.info("motion build: %s drives %s (motion=%s)", os.path.basename(motion_path),
                    assembly_ref, result.get("motion"))
        return result
