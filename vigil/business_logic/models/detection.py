from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ClassLabel(StrEnum):
    """Supported classes labels."""

    PERSON = "person"
    VEHICLE = "vehicle"


@dataclass(frozen=True)
class BoundingBox:
    """Represent the geometric extent of a detected object in a frame."""

    center_x: int
    """X-axis coordinate of the bbox centroid, in pixels from bottom left."""
    center_y: int
    """Y-axis coordinate of the bbox centroid, in pixels from bottom left."""
    width: int
    """Width of the bounding box, in pixels."""
    height: int
    """Height of the bounding box, in pixels."""


@dataclass(frozen=True)
class Prediction:
    """Output of the detection model for a single detected object."""

    bbox: BoundingBox
    """Geometric extent of the detected object."""
    confidence: float
    """Confidence score of the prediction."""
    label: ClassLabel
    """Class label of the predicted object."""


@dataclass(frozen=True)
class Detection:
    """Represent an instance detection in the domain: a prediction anchored to a frame."""

    frame_id: UUID
    """Identifier of the frame the detection was observed in."""
    frame_position: int
    """Position of the video frame the detection was observed in."""
    prediction: Prediction
    """Model output associated with this detection."""
