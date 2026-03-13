from typing import Protocol
from uuid import UUID

from vigil.business_logic.models.detection import Detection


class DetectionRepository(Protocol):
    """Interface for storing `Detection` instances in a repository."""

    def get_by_video_id(self, detection_id: UUID) -> list[Detection]:
        """Retrieve all the detections associated to a video."""
        ...
