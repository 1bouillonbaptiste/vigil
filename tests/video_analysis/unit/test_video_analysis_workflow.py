from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

import numpy as np
import numpy.typing as npt
import pytest

from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.video_analysis.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.video_analysis.business_logic.gateways.detection_model import DetectionModel
from vigil.video_analysis.business_logic.gateways.tracker import Tracker
from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.models.detection import BoundingBox, ClassLabel, Detection, Prediction
from vigil.video_analysis.business_logic.models.frame_analyzed import FrameAnalyzed
from vigil.video_analysis.business_logic.models.track import Track
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.detection_service import DetectionService
from vigil.video_analysis.business_logic.services.id_factory import IdFactory
from vigil.video_analysis.business_logic.use_cases.track_objects import TrackObjectsUseCase
from vigil.video_analysis.business_logic.use_cases.video_analysis_workflow import VideoAnalysisWorkflow

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


class SpyFrameAnalyzed:
    def __init__(self) -> None:
        self._frame_analyzed: list[FrameAnalyzed] = []

    def __call__(self, event: FrameAnalyzed) -> None:
        self._frame_analyzed.append(event)

    def to_list(self) -> list[FrameAnalyzed]:
        """Get the saved events."""
        return self._frame_analyzed.copy()


@dataclass
class ThisContext:
    """Context for testing VideoAnalysisWorkflow."""

    frame_analyzed_events: SpyFrameAnalyzed
    video_repository: StubVideoRepository
    spy_tracker: SpyTracker
    workflow: VideoAnalysisWorkflow


@pytest.fixture(scope="function")
def this_context() -> ThisContext:
    video_repository = StubVideoRepository()
    track_repository = InMemoryTrackRepository()
    domain_event_publisher = InMemoryEventPublisher()
    spy_tracker = SpyTracker()
    detection_service = DetectionService(model=FakeDetectionModel())
    track_use_case = TrackObjectsUseCase(
        track_repository=track_repository,
        tracker=spy_tracker,
    )

    frame_analyzed_events = SpyFrameAnalyzed()
    domain_event_publisher.subscribe(handler=frame_analyzed_events)

    workflow = VideoAnalysisWorkflow(
        domain_event_publisher=domain_event_publisher,
        video_repository=video_repository,
        detection_service=detection_service,
        track_use_case=track_use_case,
        batch_size=2,
    )
    return ThisContext(
        frame_analyzed_events=frame_analyzed_events,
        video_repository=video_repository,
        spy_tracker=spy_tracker,
        workflow=workflow,
    )


def test_should_process_all_frames(this_context: ThisContext) -> None:
    # Given
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([2], dtype=np.uint8))

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then
    assert this_context.frame_analyzed_events.to_list() == [
        FrameAnalyzed(video_id=VIDEO_ID, frame_position=0),
        FrameAnalyzed(video_id=VIDEO_ID, frame_position=1),
    ]


def test_should_flush_partial_batch(this_context: ThisContext) -> None:
    # Given: batch_size=2 but only 1 frame
    this_context.video_repository.add(np.array([1], dtype=np.uint8))

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then: single frame was still tracked
    assert this_context.frame_analyzed_events.to_list() == [FrameAnalyzed(video_id=VIDEO_ID, frame_position=0)]


def test_should_handle_empty_video(this_context: ThisContext) -> None:
    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then
    assert this_context.frame_analyzed_events.to_list() == []


def test_should_run_detection_per_batch(this_context: ThisContext) -> None:
    # Given: 3 frames with batch_size=2 → one full batch + one partial
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([1], dtype=np.uint8))
    this_context.video_repository.add(np.array([1], dtype=np.uint8))

    # When
    this_context.workflow.execute(VIDEO_ID)

    # Then
    assert this_context.frame_analyzed_events.to_list() == [
        FrameAnalyzed(video_id=VIDEO_ID, frame_position=0),
        FrameAnalyzed(video_id=VIDEO_ID, frame_position=1),
        FrameAnalyzed(video_id=VIDEO_ID, frame_position=2),
    ]
