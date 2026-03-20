from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pytest

from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.controllers.pipeline_controller import PipelineController
from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection
from vigil.business_logic.models.track import Track
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.detection_service import DetectionService
from vigil.business_logic.services.id_factory import IdFactory
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase

SOURCE = VideoSource(uri="test-video")


class StubVideoReader(VideoReader):
    """Controllable video reader for tests."""

    def __init__(self) -> None:
        self._frames: list[npt.NDArray[np.uint8]] = []

    def add(self, data: npt.NDArray[np.uint8]) -> None:
        self._frames.append(data)

    def read(self, source: VideoSource) -> Iterable[npt.NDArray[np.uint8]]:
        return self._frames


class FakeDetectionModel(DetectionModel):
    """Returns one fixed bbox per non-empty frame, no bbox for all-zero
    frames."""

    _PERSON_BBOX = BoundingBox(center_x=0, center_y=0, width=1, height=1, confidence=0.9, label=ClassLabel.PERSON)

    def detect(self, frames: list[npt.NDArray[np.uint8]]) -> list[list[BoundingBox]]:
        return [[self._PERSON_BBOX] if frame.any() else [] for frame in frames]


class SpyTracker(Tracker):
    """Records the detections passed to each update() call."""

    def __init__(self) -> None:
        self.called_with_detections: list[list[Detection]] = []

    def update(self, tracks: list[Track], detections: list[Detection]) -> list[tuple[Track, Detection]]:
        self.called_with_detections.append(detections)
        return []


@dataclass
class ThisContext:
    """Context for testing PipelineController."""

    video_reader: StubVideoReader
    frame_repository: InMemoryFrameRepository
    spy_tracker: SpyTracker
    controller: PipelineController


@pytest.fixture(scope="function")
def this_context() -> ThisContext:
    video_reader = StubVideoReader()
    frame_repository = InMemoryFrameRepository()
    track_repository = InMemoryTrackRepository()
    spy_tracker = SpyTracker()
    detection_service = DetectionService(model=FakeDetectionModel())
    track_use_case = TrackObjectsUseCase(
        track_repository=track_repository,
        tracker=spy_tracker,
    )
    controller = PipelineController(
        video_reader=video_reader,
        frame_repository=frame_repository,
        detection_service=detection_service,
        track_use_case=track_use_case,
        batch_size=2,
    )
    return ThisContext(
        video_reader=video_reader,
        frame_repository=frame_repository,
        spy_tracker=spy_tracker,
        controller=controller,
    )


def test_should_store_all_frames(this_context: ThisContext) -> None:
    # Given
    this_context.video_reader.add(np.array([1], dtype=np.uint8))
    this_context.video_reader.add(np.array([2], dtype=np.uint8))

    # When
    this_context.controller.execute(SOURCE)

    # Then
    frames = this_context.frame_repository.get_by_video_id(IdFactory.new_video_id(SOURCE))
    assert len(frames) == 2
    assert [f.position for f in frames] == [0, 1]


def test_should_track_frames_in_order(this_context: ThisContext) -> None:
    # Given
    this_context.video_reader.add(np.array([1], dtype=np.uint8))
    this_context.video_reader.add(np.array([1], dtype=np.uint8))

    # When
    this_context.controller.execute(SOURCE)

    # Then: tracker called twice, frame 0 before frame 1
    frames = this_context.frame_repository.get_by_video_id(IdFactory.new_video_id(SOURCE))
    assert len(this_context.spy_tracker.called_with_detections) == 2
    assert this_context.spy_tracker.called_with_detections[0][0].frame_id == frames[0].id
    assert this_context.spy_tracker.called_with_detections[1][0].frame_id == frames[1].id


def test_should_flush_partial_batch(this_context: ThisContext) -> None:
    # Given: batch_size=2 but only 1 frame
    this_context.video_reader.add(np.array([1], dtype=np.uint8))

    # When
    this_context.controller.execute(SOURCE)

    # Then: single frame was still tracked
    assert len(this_context.spy_tracker.called_with_detections) == 1


def test_should_handle_empty_video(this_context: ThisContext) -> None:
    # Given: no frames

    # When
    this_context.controller.execute(SOURCE)

    # Then
    assert this_context.frame_repository.get_by_video_id(IdFactory.new_video_id(SOURCE)) == []
    assert this_context.spy_tracker.called_with_detections == []


def test_should_run_detection_per_batch(this_context: ThisContext) -> None:
    # Given: 3 frames with batch_size=2 → one full batch + one partial
    this_context.video_reader.add(np.array([1], dtype=np.uint8))
    this_context.video_reader.add(np.array([1], dtype=np.uint8))
    this_context.video_reader.add(np.array([1], dtype=np.uint8))

    # When
    this_context.controller.execute(SOURCE)

    # Then: tracker called once per frame (3 total across 2 flush rounds)
    assert len(this_context.spy_tracker.called_with_detections) == 3
