from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.business_logic.models.detection import BoundingBox, Detection
from vigil.business_logic.models.object_class import ObjectClass
from vigil.business_logic.models.raw_frame import RawFrame
from vigil.business_logic.use_cases.detect_objects import DetectObjectsUseCase

VIDEO_ID = UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")
FRAME = RawFrame(index=0, data=b"fake-jpeg")


class FakeDetectionModel:
    """Returns a fixed list of detections for any frame."""

    def __init__(self, detections: list[Detection]) -> None:
        self._detections = detections

    def detect(self, frame: RawFrame, video_id: UUID) -> list[Detection]:
        return self._detections


@dataclass
class ThisContext:
    detection_repository: InMemoryDetectionRepository
    use_case: DetectObjectsUseCase


@pytest.fixture
def this_context() -> ThisContext:
    repo = InMemoryDetectionRepository()
    model = FakeDetectionModel(detections=[])
    return ThisContext(
        detection_repository=repo,
        use_case=DetectObjectsUseCase(detection_model=model, detection_repository=repo),
    )


def test_detections_from_frame_are_saved_to_repository():
    repo = InMemoryDetectionRepository()
    detection = Detection(
        id=uuid4(),
        video_id=VIDEO_ID,
        frame_index=0,
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
        confidence=0.9,
        object_class=ObjectClass.PERSON,
    )
    model = FakeDetectionModel(detections=[detection])
    use_case = DetectObjectsUseCase(detection_model=model, detection_repository=repo)

    use_case.execute(FRAME, VIDEO_ID)

    assert repo.get_by_video_id(VIDEO_ID) == [detection]


def test_empty_frame_produces_no_detections(this_context: ThisContext):
    this_context.use_case.execute(FRAME, VIDEO_ID)

    assert this_context.detection_repository.get_by_video_id(VIDEO_ID) == []


def test_detections_are_attributed_to_the_correct_video():
    repo = InMemoryDetectionRepository()
    target_video = UUID("aaaaaaaa-0000-0000-0000-000000000000")
    other_video = UUID("bbbbbbbb-0000-0000-0000-000000000000")
    detection = Detection(
        id=uuid4(),
        video_id=target_video,
        frame_index=0,
        bbox=BoundingBox(center_x=50, center_y=50, width=20, height=40),
        confidence=0.8,
        object_class=ObjectClass.VEHICLE,
    )
    model = FakeDetectionModel(detections=[detection])
    use_case = DetectObjectsUseCase(detection_model=model, detection_repository=repo)

    use_case.execute(FRAME, target_video)

    assert repo.get_by_video_id(target_video) == [detection]
    assert repo.get_by_video_id(other_video) == []
