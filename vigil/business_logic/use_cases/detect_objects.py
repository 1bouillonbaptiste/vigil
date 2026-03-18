from uuid import UUID

from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.gateways.detection_store import DetectionStore
from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.models.detection import Detection


class DetectObjectsUseCase:
    """Use case for detecting objects in frames."""

    def __init__(
        self,
        frame_repository: FrameRepository,
        detection_model: DetectionModel,
        detection_store: DetectionStore,
    ):
        self._frame_repository = frame_repository
        self._detection_model = detection_model
        self._detection_store = detection_store

    def execute(self, frame_id: UUID) -> None:
        """Execute the use case on a single frame."""
        frame = self._frame_repository.get_by_id(frame_id)
        bboxes = self._detection_model.detect(frame.data)
        for bbox in bboxes:
            self._detection_store.save(
                Detection(
                    video_id=frame.video_id,
                    frame_id=frame_id,
                    bbox=bbox,
                )
            )
