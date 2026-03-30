from dataclasses import dataclass
from enum import StrEnum
from typing import NewType
from uuid import UUID

from vigil.shared_kernel.models.bounding_box import BoundingBox

# Re-export so existing imports from this module continue to work.
__all__ = ["BoundingBox", "ClassLabel", "Detection", "DetectionId", "Prediction"]

DetectionId = NewType("DetectionId", UUID)
"""Detection unique identifier."""


class ClassLabel(StrEnum):
    """Supported classes labels."""

    PERSON = "person"
    VEHICLE = "vehicle"


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

    id: DetectionId
    """Unique identifier for this detection."""
    frame_id: UUID
    """Identifier of the frame the detection was observed in."""
    frame_position: int
    """Position of the video frame the detection was observed in."""
    prediction: Prediction
    """Model output associated with this detection."""
