"""Raised when a kernel operation fails after the robustness ladder is exhausted."""


class KernelOpError(Exception):
    """A geometry operation (boolean, fillet, chamfer) failed to produce a valid result.

    The build123d kernel raises this after its retry/heal ladder gives up; ops catch it
    and turn it into an id-tagged BuildIssue rather than crashing the build.
    """
