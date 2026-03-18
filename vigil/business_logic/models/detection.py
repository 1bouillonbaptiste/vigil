from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ClassLabel(StrEnum):
    """Supported classes labels."""

    PEOPLE = "people"
    VEHICLE = "vehicle"


@dataclass(frozen=True)
class BoundingBox:
    """Represent the bounding box around a detected object."""

    center_x: int
    """X-axis coordinate of the bbox centroid, in pixels from bottom left."""
    center_y: int
    """Y-axis coordinate of the bbox centroid, in pixels from bottom left."""
    width: int
    """Width of the bounding box, in pixels."""
    height: int
    """Height of the bounding box, in pixels."""
    confidence: float
    """Confidence score of the bounding box."""
    label: ClassLabel
    """Class label of the bounding box."""


@dataclass(frozen=True)
class Detection:
    """Represent an instance detection object."""

    id: UUID
    """Identifier of the detection."""

    frame_id: UUID
    """Identifier of the frame the detection was detected in."""

    bbox: BoundingBox
    """Bounding box around the detection."""
