from dataclasses import dataclass, replace
from uuid import UUID, uuid4

import pytest
from pytest_cases import parametrize_with_cases

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection
from vigil.business_logic.models.frame import VideoFrame
from vigil.business_logic.use_cases.detect_objects import DetectObjectsUseCase


class StubDetectionModel(DetectionModel):
    """Store detections for testing purpose.

    Each item represents the detections associated to a frame id.
    """

    def __init__(self) -> None:
        self._detections: dict[UUID, list[BoundingBox]] = {
            UUID("8d672f18-906e-4ff9-a06d-938898683720"): [],
            UUID("8d672f18-906e-4ff9-a06d-938898683721"): [
                BoundingBox(center_x=0, center_y=0, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE)
            ],
        }

    def detect(self, frame: VideoFrame) -> list[BoundingBox]:
        """Return the detections associated to a frame id."""
        return self._detections[frame.id]


@dataclass
class ThisContext:
    """Context for testing `DetectObjectsUseCase`."""

    frame_repository: InMemoryFrameRepository
    detection_model: StubDetectionModel
    detection_repository: InMemoryDetectionRepository
    use_case: DetectObjectsUseCase


@pytest.fixture
def this_context() -> ThisContext:
    frame_repository = InMemoryFrameRepository()
    detection_model = StubDetectionModel()
    detection_repository = InMemoryDetectionRepository()
    use_case = DetectObjectsUseCase(
        frame_repository=frame_repository, detection_model=detection_model, detection_repository=detection_repository
    )
    return ThisContext(
        frame_repository=frame_repository,
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
        return UUID("8d672f18-906e-4ff9-a06d-938898683720"), []

    def case_one_people(self):
        return UUID("8d672f18-906e-4ff9-a06d-938898683721"), [
            Detection(
                id=uuid4(),  # will be replaced
                frame_id=UUID("8d672f18-906e-4ff9-a06d-938898683721"),
                bbox=BoundingBox(center_x=0, center_y=0, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE),
            )
        ]


@parametrize_with_cases("frame_id, expected_detections", cases=ShouldDetectOnFrameCases)
def test_should_detect_on_frame(
    this_context: ThisContext, frame_id: UUID, expected_detections: list[Detection]
) -> None:
    # Given
    this_context.frame_repository.save(
        VideoFrame(
            id=UUID("8d672f18-906e-4ff9-a06d-938898683720"),
            position=0,
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
        )
    )
    this_context.frame_repository.save(
        VideoFrame(
            id=UUID("8d672f18-906e-4ff9-a06d-938898683721"),
            position=1,
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
        )
    )

    # When
    this_context.use_case.execute(frame_id=frame_id)

    # Then
    detections: list[Detection] = []
    for frame in this_context.frame_repository.get_by_video_id(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")):
        detections.extend(this_context.detection_repository.get_by_frame_id(frame_id=frame.id))
    assert len(detections) == len(expected_detections)
    for detection, expected in zip(detections, expected_detections, strict=True):
        assert detection == replace(expected, id=detection.id)
