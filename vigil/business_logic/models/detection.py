

from dataclasses import dataclass

@dataclass(frozen=True)
class Detection:
    """Represent an instance detection object."""

    detection_id: int
    """Identifier of the detection."""