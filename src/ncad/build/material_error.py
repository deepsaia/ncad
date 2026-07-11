"""The typed error for material library / resolution / mass-property contract violations."""


class MaterialError(Exception):
    """A material is unknown, malformed, or lacks a property needed for a derived quantity."""
