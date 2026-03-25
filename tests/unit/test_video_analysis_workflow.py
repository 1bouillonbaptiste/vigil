from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

import numpy as np
import numpy.typing as npt
import pytest

from vigil.adapters.secondary.in_memory_domain_event_publisher import InMemoryDomainEventPublisher
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.gateways.video_repository import VideoRepository
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection, Prediction
from vigil.business_logic.models.frame_analyzed import FrameAnalyzed
from vigil.business_logic.models.track import Track
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.analysis_progress_projection import AnalysisProgressProjection
from vigil.business_logic.services.detection_service import DetectionService
from vigil.business_logic.services.id_factory import IdFactory
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase
from vigil.business_logic.use_cases.video_analysis_workflow import VideoAnalysisWorkflow

VIDEO_ID = IdFactory.new_video_id(VideoSource(uri="test-video"))


class StubVideoRepository(VideoRepository):
    """Controllable video repository for tests."""

    def __init__(self) -> None:
        self._frames: list[npt.NDArray[np.uint8]] = []

    def add(self, data: npt.NDArray[np.uint8]) -> None:
        self._frames.append(data)

    def save(self, source: VideoSource, data: bytes) -> None:
        pass

    def read(self, video_id: UUID) -> Iterable[npt.NDArray[np.uint8]]:
        return self._frames

    def frame_count(self, video_id: UUID) -> int:
        return len(self._frames)


class FakeDetectionModel(DetectionModel):
    """Returns one fixed prediction per non-empty frame, no prediction for all-
    zero frames."""

    _PERSON_PREDICTION = Prediction(
        bbox=BoundingBox(center_x=0, center_y=0, width=1, height=1),
        confidence=0.9,
        label=ClassLabel.PERSON,
    )

    def detect(self, frames: list[npt.NDArray[np.uint8]]) -> list[list[Prediction]]:
        return [[self._PERSON_PREDICTION] if frame.any() else [] for frame in frames]


class SpyTracker(Tracker):
    """Records the detections passed to each update() call."""

    def __init__(self) -> None:
        self.called_with_detections: list[list[Detection]] = []

    def update(self, tracks: list[Track], detections: list[Detection]) -> list[tuple[Track, Detection]]:
        self.called_with_detections.append(detections)
        return []


@dataclass
class ThisContext:
    """Context for testing VideoAnalysisWorkflow."""

    video_repository: StubVideoRepository
    publisher: InMemoryDomainEventPublisher[FrameAnalyzed]
    progress_projection: AnalysisProgressProjection
    spy_tracker: SpyTracker
    workflow: VideoAnalysisWorkflow


@pytest.fixture(scope="function")
def this_context() -> ThisContext:
    video_repository = StubVideoRepository()
    publisher: InMemoryDomainEventPublisher[FrameAnalyzed] = InMemoryDomainEventPublisher()
    progress_projection = AnalysisProgressProjection()
    publisher.subscribe(progress_projection)
    track_repository = InMemoryTrackRepository()
    spy_tracker = SpyTracker()
    detection_service = DetectionService(model=FakeDetectionModel())
    track_use_case = TrackObjectsUseCase(
        track_repository=track_repository,
        tracker=spy_tracker,
    )
    workflow = VideoAnalysisWorkflow(
        video_repository=video_repository,
        publisher=publisher,
        detection_service=detection_service,
        track_use_case=track_use_case,
        batch_size=2,
    )
    return ThisContext(
        video_repository=video_repository,
        publisher=publisher,
        progress_projection=progress_projection,
        spy_tracker=spy_tracker,
        workflow=workflow,
    )


def test_should_publish_one_event_per_frame(this_context: ThisContext) -> None:
    # Given
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([2], dtype=np.uint8))

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then
    assert this_context.progress_projection.count(VIDEO_ID) == 2


def test_should_publish_events_with_correct_positions(this_context: ThisContext) -> None:
    # Given
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([2], dtype=np.uint8))
    received: list[FrameAnalyzed] = []
    this_context.publisher.subscribe(received.append)

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then
    assert [e.position for e in received] == [0, 1]


def test_should_track_frames_in_order(this_context: ThisContext) -> None:
    # Given
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([1], dtype=np.uint8))

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then: tracker called twice, frame 0 before frame 1
    expected_frame_id_0 = IdFactory.new_frame_id(video_id=VIDEO_ID, position=0)
    expected_frame_id_1 = IdFactory.new_frame_id(video_id=VIDEO_ID, position=1)
    assert len(this_context.spy_tracker.called_with_detections) == 2
    assert this_context.spy_tracker.called_with_detections[0][0].frame_id == expected_frame_id_0
    assert this_context.spy_tracker.called_with_detections[1][0].frame_id == expected_frame_id_1


def test_should_flush_partial_batch(this_context: ThisContext) -> None:
    # Given: batch_size=2 but only 1 frame
    this_context.video_repository.add(np.array([1], dtype=np.uint8))

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then: single frame was still tracked
    assert len(this_context.spy_tracker.called_with_detections) == 1


def test_should_handle_empty_video(this_context: ThisContext) -> None:
    # Given: no frames

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then
    assert this_context.progress_projection.count(VIDEO_ID) == 0
    assert this_context.spy_tracker.called_with_detections == []


def test_should_run_detection_per_batch(this_context: ThisContext) -> None:
    # Given: 3 frames with batch_size=2 → one full batch + one partial
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([1], dtype=np.uint8))

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then: tracker called once per frame (3 total across 2 flush rounds)
    assert len(this_context.spy_tracker.called_with_detections) == 3
