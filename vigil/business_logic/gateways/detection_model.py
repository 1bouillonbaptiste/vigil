from typing import Protocol
from uuid import UUID

from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.raw_frame import RawFrame


class DetectionModel(Protocol):
    """Interface for a deep-learning object detection model.

    Implementations run inference on a single video frame and return
    domain Detection objects. All infrastructure concerns (e.g. COCO class
    IDs, numpy arrays) are handled internally by the adapter.
    """

    def detect(self, frame: RawFrame, video_id: UUID) -> list[Detection]:
        """Detect objects in a single frame.

        Returns an empty list if no supported objects are found.
        """
        ...
