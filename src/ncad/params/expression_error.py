"""Error raised when a parameter expression is malformed or disallowed."""


class ExpressionError(Exception):
    """A parameter expression could not be resolved.

    Raised for unknown references, disallowed syntax, unknown functions, or
    reference cycles. This is a contract error (the document is malformed), so it is
    raised rather than returned as data.
    """
