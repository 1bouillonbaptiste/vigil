from uuid import UUID

from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.frame_store import FrameStore
from vigil.business_logic.models.detection import Detection
from vigil.business_logic.services.id_factory import IdFactory


class DetectObjectsUseCase:
    """Use case for detecting objects in frames."""

    def __init__(
        self,
        frame_repository: FrameRepository,
        frame_store: FrameStore,
        detection_model: DetectionModel,
        detection_repository: DetectionRepository,
    ):
        self._frame_repository = frame_repository
        self._frame_store = frame_store
        self._detection_model = detection_model
        self._detection_repository = detection_repository

    def execute(self, frame_id: UUID) -> None:
        """Execute the use case on a single frame."""
        frame = self._frame_repository.get_by_id(frame_id)
        data = self._frame_store.load(frame)
        bboxes = self._detection_model.detect(data)
        for bbox in bboxes:
            self._detection_repository.save(
                Detection(
                    id=IdFactory.new_detection_id(frame_id=frame_id, bbox=bbox),
                    frame_id=frame_id,
                    bbox=bbox,
                )
            )
