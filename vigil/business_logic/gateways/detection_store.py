from typing import Protocol
from uuid import UUID

from vigil.business_logic.models.detection import Detection


class DetectionStore(Protocol):
    """Ephemeral store for `Detection` instances..

    Exists as the handoff point between detection and tracking, which have different
    execution models: detection is embarrassingly parallel (each frame is independent)
    while tracking must be sequential (frames must be processed in order). Detection
    workers write concurrently; the tracker drains one frame at a time then clears.
    If parallel detection is never needed, this store and the two use cases can be
    merged into a single detect-and-track use case.
    """

    def get_by_frame_id(self, frame_id: UUID) -> list[Detection]:
        """Retrieve all the detections associated to a frame."""
        ...

    def save(self, detection: Detection) -> None:
        """Save the detection to the store."""
        ...

    def clear(self) -> None:
        """Clear all detections from the store."""
        ...
