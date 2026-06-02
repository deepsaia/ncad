"""Phase 0 smoke tests: verify the core dependency wheels actually import.

Dry-run resolution proves a compatible wheel exists; this proves it loads in the
target interpreter (Python 3.13). These are intentionally minimal — they guard the
environment, not behavior.
"""

import importlib

import pytest

CORE_MODULES = [
    "build123d",
    "OCP",  # OpenCASCADE binding pulled by build123d
    "jsonschema",
    "leaf_common",
    "numpy",
    "trimesh",
]


@pytest.mark.parametrize("module_name", CORE_MODULES)
def test_core_dependency_imports(module_name: str) -> None:
    """Each core dependency imports without error."""
    importlib.import_module(module_name)


def test_leaf_common_easy_persistence_available() -> None:
    """The leaf-common persistence classes we build the spec layer on are importable."""
    from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence
    from leaf_common.persistence.easy.easy_json_persistence import EasyJsonPersistence

    assert hasattr(EasyHoconPersistence, "restore")
    assert hasattr(EasyJsonPersistence, "restore")


def test_ncad_package_imports() -> None:
    """The ncad package itself imports."""
    import ncad

    assert ncad is not None
