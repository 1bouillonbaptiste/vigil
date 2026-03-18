from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID

import numpy as np
import pytest
from pytest_cases import parametrize_with_cases

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_frame_store import InMemoryFrameStore
from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.models.detection import BoundingBox, ClassLabel
from vigil.business_logic.models.frame import FrameData, FrameId, VideoFrame
from vigil.business_logic.use_cases.detect_objects import DetectObjectsUseCase


class FakeDetectionModel(DetectionModel):
    """Fake implementation for testing purpose.

    The model detects a bbox of size 1 for each non-zero pixel.
    """

    _class_mapping: ClassVar[dict[int, ClassLabel]] = {
        1: ClassLabel.PEOPLE,
        2: ClassLabel.VEHICLE,
    }

    def detect(self, frame: FrameData) -> list[BoundingBox]:
        """Return the detections associated to a frame id."""
        num_rows = frame.data.shape[0]
        return [
            BoundingBox(
                center_x=int(col),
                center_y=int(num_rows - 1 - row),
                width=1,
                height=1,
                confidence=0.5,
                label=label,
            )
            for row, col in np.argwhere(frame.data != 0)
            if (label := self._class_mapping.get(frame.data[row, col].item())) is not None
        ]


@dataclass
class ThisContext:
    """Context for testing `DetectObjectsUseCase`."""

    frame_repository: InMemoryFrameRepository
    frame_store: InMemoryFrameStore
    detection_model: FakeDetectionModel
    detection_repository: InMemoryDetectionRepository
    use_case: DetectObjectsUseCase


@pytest.fixture
def this_context() -> ThisContext:
    frame_repository = InMemoryFrameRepository()
    frame_store = InMemoryFrameStore()
    detection_model = FakeDetectionModel()
    detection_repository = InMemoryDetectionRepository()
    use_case = DetectObjectsUseCase(
        frame_repository=frame_repository,
        frame_store=frame_store,
        detection_model=detection_model,
        detection_repository=detection_repository,
    )
    return ThisContext(
        frame_repository=frame_repository,
        frame_store=frame_store,
        detection_model=detection_model,
        detection_repository=detection_repository,
        use_case=use_case,
    )


class ShouldDetectOnFrameCases:
    """Generate cases for `test_should_detect_on_frame`.

    Each case returns:
    - a frame index to run detection on
    - the expected detections
    """

    def case_empty_detections(self):
        frame = VideoFrame(
            id=FrameId(UUID("8d672f18-906e-4ff9-a06d-938898683720")),
            position=0,
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
        )
        data = FrameData(data=np.array([0, 0], dtype=np.uint8))
        return frame, data, []

    def case_one_people(self):
        frame = VideoFrame(
            id=FrameId(UUID("8d672f18-906e-4ff9-a06d-938898683721")),
            position=1,
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
        )
        data = FrameData(data=np.array([[0, 0], [1, 0]], dtype=np.uint8))
        return (
            frame,
            data,
            [BoundingBox(center_x=0, center_y=0, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE)],
        )

    def case_one_people_one_vehicle(self):
        frame = VideoFrame(
            id=FrameId(UUID("8d672f18-906e-4ff9-a06d-938898683721")),
            position=1,
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
        )
        data = FrameData(data=np.array([[0, 2], [1, 0]], dtype=np.uint8))
        return (
            frame,
            data,
            [
                BoundingBox(center_x=1, center_y=1, width=1, height=1, confidence=0.5, label=ClassLabel.VEHICLE),
                BoundingBox(center_x=0, center_y=0, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE),
            ],
        )


@parametrize_with_cases("frame, data, expected_detections", cases=ShouldDetectOnFrameCases)
def test_should_detect_on_frame(
    this_context: ThisContext, frame: VideoFrame, data: FrameData, expected_detections: list[BoundingBox]
) -> None:
    # Given
    this_context.frame_repository.save(frame)
    this_context.frame_store.store(frame, data)

    # When
    this_context.use_case.execute(frame_id=frame.id)

    # Then
    detections = this_context.detection_repository.get_by_frame_id(frame_id=frame.id)
    assert {detection.bbox for detection in detections} == set(expected_detections)
