"""Compose an assembly document into a scene sidecar the viewer renders.

For each instance: build (or reuse, via a per-file DocumentBuilder + its feature cache) the
referenced part's glb, resolve its placement to a 4x4, and record it. The result is a lightweight
composition of independently-built cached parts (design section 7 large-assembly strategy), NOT a
re-baked merged glTF. Bad instance refs are id-attributed issues; a bad instance is skipped and
the rest still compose (an assembly is partially viewable).
"""

import json
import logging
import os
from typing import Any

from ncad.assembly.assembly_placement import AssemblyPlacement
from ncad.build.document_builder import DocumentBuilder
from ncad.spec.assembly_schema_validator import AssemblySchemaValidator
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_ASSEMBLY_SUFFIX = ".assembly.json"
# Document unit -> metres (glTF's unit). The scene sidecar's placements are baked to metres so
# they match the part glbs (which export in metres), and the viewer stays unit-agnostic.
_TO_METRES = {"mm": 0.001, "m": 1.0, "in": 0.0254}


class AssemblyBuilder:
    """Builds/reuses each instance's part glb and writes the assembly scene sidecar."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel
        self._loader = SpecLoader()
        self._validator = AssemblySchemaValidator()
        self._placement = AssemblyPlacement()

    def assemble(self, asm_path: str, out_dir: str) -> dict:
        """Compose the assembly at ``asm_path`` into ``out_dir``; return sidecar path + issues."""
        document = self._loader.load(asm_path)
        schema_issues = self._validator.validate(document)
        if schema_issues:
            rendered = "; ".join(f"{i.location}: {i.message}" for i in schema_issues)
            raise ValueError(f"assembly failed schema validation: {rendered}")
        os.makedirs(out_dir, exist_ok=True)
        asm_dir = os.path.dirname(os.path.abspath(asm_path))
        name = _stem(asm_path)
        # Part glbs export in metres (build123d export_gltf scales the document unit to metres),
        # so the scene sidecar bakes placements to metres too. The viewer then consumes the scene
        # unit-agnostic, exactly as it does a single-part glb.
        to_metres = _TO_METRES.get(document.get("units", "mm"), 0.001)
        # One DocumentBuilder per part file so its feature cache composes cached parts across
        # instances; built_glbs dedups a {file, part} placed more than once.
        builders: dict[str, DocumentBuilder] = {}
        built_glbs: dict[tuple[str, str], str] = {}
        instances: list[dict] = []
        issues: list[dict] = []
        for instance in document["assembly"]["instances"]:
            glb = self._ensure_part_glb(instance, asm_dir, out_dir, builders, built_glbs, issues)
            if glb is None:
                continue
            matrix = self._placement.matrix(instance.get("placement"), to_metres)
            instances.append({"id": instance["id"], "part_glb": glb,
                              "part_name": instance["part"], "placement": matrix})
        sidecar = os.path.join(out_dir, f"{name}{_ASSEMBLY_SUFFIX}")
        # Record the source .asm.hocon so the viewer can regenerate this assembly after a reload
        # (the browser's in-memory source map is lost on reload; this survives it, like the part
        # meta sidecar's `source`).
        with open(sidecar, "w", encoding="utf-8") as handle:
            json.dump({"schema_version": 1, "name": name, "source": os.path.abspath(asm_path),
                       "instances": instances}, handle)
        return {"sidecar": sidecar, "issues": issues, "instances": [i["id"] for i in instances]}

    def _ensure_part_glb(self, instance: dict, asm_dir: str, out_dir: str,
                         builders: dict, built_glbs: dict, issues: list) -> str | None:
        """Build or reuse the glb for one instance's {file, part}; return its glb basename."""
        instance_id = instance["id"]
        part_file = os.path.join(asm_dir, instance["file"])
        part_name = instance["part"]
        key = (os.path.abspath(part_file), part_name)
        if key in built_glbs:
            return built_glbs[key]  # this {file, part} already built: reuse the glb (dedup)
        if not os.path.exists(part_file):
            issues.append({"instance_id": instance_id,
                           "message": f"part file not found: {instance['file']!r}"})
            return None
        builder = builders.setdefault(key[0], DocumentBuilder(self._kernel))
        try:
            artifacts = builder.build_file(part_file, out_dir, formats=("glb",))
        except Exception as exc:  # noqa: BLE001 - a bad part becomes an id-attributed issue
            issues.append({"instance_id": instance_id, "message": f"part build failed: {exc}"})
            return None
        if part_name not in artifacts:
            issues.append({"instance_id": instance_id,
                           "message": f"part {part_name!r} not in {instance['file']!r}"})
            return None
        glb = os.path.basename(artifacts[part_name])
        built_glbs[key] = glb
        return glb


def _stem(path: str) -> str:
    """The assembly name: the basename without the .asm.hocon (or .hocon) extension."""
    base = os.path.basename(path)
    for suffix in (".asm.hocon", ".hocon"):
        if base.lower().endswith(suffix):
            return base[: -len(suffix)]
    return base
