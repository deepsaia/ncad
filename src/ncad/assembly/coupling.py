"""A declarative coupling between two joints (bucket 5.4b): gear / belt / rack_pinion / universal.

A coupling relates two JOINTS (not connectors) by a rate/position ratio; it positions nothing and
adds no solve primitives. 5.4b stores + validates + surfaces it; Phase 6 enforces it (driving one
joint so the coupled joint follows, forward kinematics). Pure data.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Coupling:
    """One declared joint-to-joint coupling (enforced during motion, Phase 6).

    ``profile`` is a curve reference for a ``cam`` coupling (the cam profile the follower rides);
    None for the rate-ratio couplings (gear/belt/rack_pinion/universal). Bucket 5.7.
    """

    id: str
    type: str
    between: list[str]
    ratio: float | None = None
    profile: str | None = None

    def to_dict(self) -> dict:
        """A JSON-serializable record for the sidecar couplings block."""
        return {"id": self.id, "type": self.type, "between": list(self.between),
                "ratio": self.ratio, "profile": self.profile}
