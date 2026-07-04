"""Raised when a selector string is malformed or names an unknown attribute."""


class SelectorError(Exception):
    """A selector query could not be parsed or referenced an unknown attribute."""
