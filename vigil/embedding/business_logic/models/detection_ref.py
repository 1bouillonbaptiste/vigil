from dataclasses import dataclass
from uuid import UUID

from vigil.shared_kernel.models.bounding_box import BoundingBox


@dataclass(frozen=True)
class DetectionRef:
    """A detection as seen by the embedding context: id, location, and frame."""

    detection_id: UUID
    """Detection unique identifier."""
    frame_position: int
    """Position of the frame the detection was observed in."""
    bbox: BoundingBox
    """Bounding box of the detection in that frame."""
