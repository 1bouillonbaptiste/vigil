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

    @property
    def area(self) -> float:
        """Bbox area in squared pixels."""
        return self.width * self.height

    @property
    def bottom_left(self) -> tuple[int, int]:
        """Coordinates of the bottom left corner pixel."""
        return self.center_x - self.width // 2, self.center_y - self.height // 2

    @property
    def top_right(self) -> tuple[int, int]:
        """Coordinates of the top right corner pixel."""
        _odd_width = self.width % 2
        _odd_height = self.height % 2
        return self.center_x + self.width // 2 + _odd_width, self.center_y + self.height // 2 + _odd_height


@dataclass(frozen=True)
class Detection:
    """Represent an instance detection object."""

    id: UUID
    """Identifier of the detection."""

    frame_id: UUID
    """Identifier of the frame the detection was detected in."""

    bbox: BoundingBox
    """Bounding box around the detection."""

    def score(self) -> float:
        """Visibility score, the larger the area and the higher the confidence, the best."""
        return self.bbox.confidence * self.bbox.area
