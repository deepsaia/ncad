"""SlicerLocator finds the first available slicer by preference and builds the right argv."""

from ncad.cam import slicer_locator
from ncad.cam.slicer_locator import SlicerLocator


def test_locate_returns_first_available_in_preference(monkeypatch):
    # Only prusa-slicer is on PATH; preference [orca, prusa] skips the absent orca.
    monkeypatch.setattr(
        slicer_locator.shutil, "which",
        lambda name: "/usr/bin/prusa-slicer" if name == "prusa-slicer" else None)
    located = SlicerLocator().locate(("orca", "prusa"))
    assert located == {"slicer": "prusa", "binary": "/usr/bin/prusa-slicer", "dialect": "slic3r"}


def test_locate_returns_none_when_no_slicer(monkeypatch):
    monkeypatch.setattr(slicer_locator.shutil, "which", lambda name: None)
    assert SlicerLocator().locate(("orca", "prusa", "cura")) is None


def test_slic3r_argv_shape():
    argv = SlicerLocator().argv(
        "/bin/prusa-slicer", "slic3r", "cfg.ini", "m.stl", "out.gcode", ["--support-material"])
    assert argv == ["/bin/prusa-slicer", "--load", "cfg.ini", "--export-gcode",
                    "--output", "out.gcode", "--support-material", "m.stl"]


def test_cura_argv_shape():
    argv = SlicerLocator().argv("/bin/CuraEngine", "cura", "printer.json", "m.stl", "out.gcode", [])
    assert argv == ["/bin/CuraEngine", "slice", "-j", "printer.json", "-l", "m.stl",
                    "-o", "out.gcode"]
