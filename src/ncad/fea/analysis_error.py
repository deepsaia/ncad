"""The typed error the FEA document layer raises for a genuine analysis-run fault.

Distinct from AnalysisParamError (vocabulary/contract violations, raised during parse and
surfaced as structured diagnostics) and from the delegation report's skipped/failed status
(a missing or failing external tool). AnalysisError is for a real fault inside a run that has
already passed validation (e.g. the built part exported no solid to mesh).
"""


class AnalysisError(Exception):
    """A structural-analysis run failed for a reason that is neither a contract violation nor a
    delegated-tool outcome."""
