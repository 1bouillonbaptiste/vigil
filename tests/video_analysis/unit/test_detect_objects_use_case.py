from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

import numpy as np
import numpy.typing as npt
import pytest

from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.video_analysis.business_logic.gateways.detection_model import DetectionModel
from vigil.video_analysis.business_logic.models.detection import BoundingBox, ClassLabel, Prediction
from vigil.video_analysis.business_logic.models.frame_detected import FrameDetected
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.detection_service import DetectionService
from vigil.video_analysis.business_logic.services.id_factory import IdFactory
from vigil.video_analysis.business_logic.use_cases.detect_objects import DetectObjectsUseCase

VIDEO_ID = IdFactory.new_video_id(VideoSource(uri="test-video"))

_PERSON_PREDICTION = Prediction(
    bbox=BoundingBox(center_x=10, center_y=10, width=5, height=5),
    confidence=0.9,
    label=ClassLabel.PERSON,
)


class StubVideoRepository:
    """Controllable video repository for tests."""

    def __init__(self) -> None:
        self._frames: list[npt.NDArray[np.uint8]] = []

    def add(self, data: npt.NDArray[np.uint8]) -> None:
        self._frames.append(data)

    def save(self, source: object, data: bytes) -> None:
        pass

    def read(self, video_id: UUID) -> Iterable[npt.NDArray[np.uint8]]:
        return self._frames

    def frame_count(self, video_id: UUID) -> int:
        return len(self._frames)


class FakeDetectionModel(DetectionModel):
    """Returns _PERSON_PREDICTION for non-zero frames, nothing for zero
    frames."""

    def detect(self, frames: list[npt.NDArray[np.uint8]]) -> list[list[Prediction]]:
        return [[_PERSON_PREDICTION] if frame.any() else [] for frame in frames]


class SpyFrameDetected:
    def __init__(self) -> None:
        self._events: list[FrameDetected] = []

    def __call__(self, event: FrameDetected) -> None:
        self._events.append(event)

    def to_list(self) -> list[FrameDetected]:
        return self._events.copy()


@dataclass
class ThisContext:
    frame_detected_events: SpyFrameDetected
    video_repository: StubVideoRepository
    use_case: DetectObjectsUseCase


@pytest.fixture
def this_context() -> ThisContext:
    video_repository = StubVideoRepository()
    domain_event_publisher = InMemoryEventPublisher()
    detection_service = DetectionService(model=FakeDetectionModel())

    frame_detected_events = SpyFrameDetected()
    domain_event_publisher.subscribe(handler=frame_detected_events)

    use_case = DetectObjectsUseCase(
        domain_event_publisher=domain_event_publisher,
        video_repository=video_repository,
        detection_service=detection_service,
        batch_size=2,
    )
    return ThisContext(
        frame_detected_events=frame_detected_events,
        video_repository=video_repository,
        use_case=use_case,
    )


def test_should_return_empty_list_for_empty_video(this_context: ThisContext) -> None:
    result = this_context.use_case.execute(VIDEO_ID)

    assert result == []


def test_should_publish_no_events_for_empty_video(this_context: ThisContext) -> None:
    this_context.use_case.execute(VIDEO_ID)

    assert this_context.frame_detected_events.to_list() == []


def test_should_return_detections_for_non_zero_frames(this_context: ThisContext) -> None:
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([1], dtype=np.uint8))

    result = this_context.use_case.execute(VIDEO_ID)

    assert len(result) == 2


def test_should_return_no_detections_for_zero_frames(this_context: ThisContext) -> None:
    this_context.video_repository.add(np.zeros(1, dtype=np.uint8))

    result = this_context.use_case.execute(VIDEO_ID)

    assert result == []


def test_should_publish_one_event_per_frame(this_context: ThisContext) -> None:
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([2], dtype=np.uint8))

    this_context.use_case.execute(VIDEO_ID)

    assert this_context.frame_detected_events.to_list() == [
        FrameDetected(video_id=VIDEO_ID, frame_position=0),
        FrameDetected(video_id=VIDEO_ID, frame_position=1),
    ]


def test_should_flush_partial_batch(this_context: ThisContext) -> None:
    # batch_size=2 but only 1 frame — must still process
    this_context.video_repository.add(np.array([1], dtype=np.uint8))

    this_context.use_case.execute(VIDEO_ID)

    assert this_context.frame_detected_events.to_list() == [
        FrameDetected(video_id=VIDEO_ID, frame_position=0),
    ]


def test_should_collect_detections_across_batches(this_context: ThisContext) -> None:
    # 3 frames with batch_size=2 → two flushes
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([1], dtype=np.uint8))

    result = this_context.use_case.execute(VIDEO_ID)

    assert len(result) == 3
