from uuid import UUID, uuid4
from dataclasses import replace

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.business_logic.models.detection import Detection, BoundingBox
from vigil.business_logic.use_cases.detect_objects import DetectObjectsUseCase


def test_should_detect_a_person():
    # Given
    detection_repository = InMemoryDetectionRepository()
    use_case = DetectObjectsUseCase(detection_repository=detection_repository)


    # When
    use_case.execute()

    # Then
    detections = detection_repository.get_by_video_id(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(detections) == 1
    assert detections[0] == Detection(
        id=detections[0].id,
        video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
        frame_index=0,
        bbox=BoundingBox(center_x=0, center_y=0, width=1, height=1),
        confidence=0.5,
    )

