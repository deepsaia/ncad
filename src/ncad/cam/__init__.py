"""CAM delegation: slice an STL to G-code via an installed slicer (none bundled)."""

from ncad.cam.gcode_validator import GcodeValidator
from ncad.cam.slice_runner import SliceRunner
from ncad.cam.slicer_locator import SlicerLocator
from ncad.cam.slicer_profile import SlicerProfile

__all__ = ["GcodeValidator", "SliceRunner", "SlicerLocator", "SlicerProfile"]
