"""Static material-reference check for a part document (bucket: validation & diagnostics).

Catches a material name that does not resolve to any known material - the part-level default
(``parts.<name>.material``) or a per-feature override (``parts.<name>.features[].material``) -
which today only surfaces as a mid-build MaterialError. The resolvable material names (seed +
document-inline + external library) are supplied by the caller as ``known_materials`` (mirroring
how AssemblyReferenceCheck receives connectors_by_part), so this layer stays side-effect-free and
needs no file IO. A missing material (none declared) is NOT an error: a body may inherit a default
or stay uncolored. Returns Diagnostics; never raises. One class.
"""

from ncad.diagnostics import codes
from ncad.diagnostics.diagnostic import Diagnostic


class MaterialReferenceCheck:
    """Validates part/feature material references against the resolvable material names."""

    def check(self, document: dict, known_materials: set) -> list[Diagnostic]:
        """Return UNKNOWN_REFERENCE Diagnostics for material names that do not resolve."""
        out: list[Diagnostic] = []
        parts = document.get("parts") or {}
        for part_name, part in parts.items():
            if not isinstance(part, dict):
                continue
            self._check_ref(part.get("material"), known_materials,
                            f"parts.{part_name}.material", out)
            for fidx, feature in enumerate(part.get("features") or []):
                if not isinstance(feature, dict):
                    continue
                self._check_ref(feature.get("material"), known_materials,
                                f"parts.{part_name}.features.{fidx}.material", out)
        return out

    def _check_ref(self, name: object, known_materials: set, location: str,
                   out: list[Diagnostic]) -> None:
        """Append a Diagnostic when ``name`` is a non-empty string that does not resolve."""
        if not isinstance(name, str) or not name:
            return
        if name in known_materials:
            return
        out.append(Diagnostic(
            severity="error", code=codes.UNKNOWN_REFERENCE, location=location,
            message=f"references unknown material {name!r}",
            hint="declare it in the document 'materials' block / 'materials_library', "
                 "or use a seed material name",
            stage="semantic"))
