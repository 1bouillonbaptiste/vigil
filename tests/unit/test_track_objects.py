from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.iou_tracker import IouTracker
from vigil.business_logic.models.detection import BoundingBox, ClassLabel
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase

from tests.helpers import DetectionFactory


@dataclass
class ThisContext:
    """Testing context for `TrackObjectsUseCase`."""

    frame_repository: InMemoryFrameRepository
    detection_repository: InMemoryDetectionRepository
    tracker: IouTracker
    track_repository: InMemoryTrackRepository
    use_case: TrackObjectsUseCase


@pytest.fixture
def this_context() -> ThisContext:
    frame_repository = InMemoryFrameRepository()
    detection_repository = InMemoryDetectionRepository()
    tracker = IouTracker()
    track_repository = InMemoryTrackRepository()
    use_case = TrackObjectsUseCase(
        frame_repository=frame_repository,
        detection_repository=detection_repository,
        tracker=tracker,
        track_repository=track_repository,
    )
    return ThisContext(
        frame_repository=frame_repository,
        detection_repository=detection_repository,
        tracker=tracker,
        track_repository=track_repository,
        use_case=use_case,
    )


def test_should_remove_track_with_fewer_than_5_detections(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository, detection_repository=this_context.detection_repository
    )
    factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    factory.create(at_position=0)
    factory.create(at_position=1)
    factory.create(at_position=2)
    factory.create(at_position=3)

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")) == []


def test_should_track_an_object_appearing_more_than_5_times_included(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository,
        detection_repository=this_context.detection_repository,
    )
    factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Valid track with 5 detections
    factory.create(at_position=0)
    factory.create(at_position=1)
    factory.create(at_position=2)
    factory.create(at_position=3)
    factory.create(at_position=4)

    # Invalid track with 3 detections
    factory.create(at_position=8)
    factory.create(at_position=9)
    factory.create(at_position=10)

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].video_id == UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")
    assert len(tracks[0].detections) == 5


def test_should_select_largest_detection_as_best_on_same_confidence(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository, detection_repository=this_context.detection_repository
    )
    factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    factory.create(at_position=0)
    largest_detection = factory.create(
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=35, confidence=0.8, label=ClassLabel.PEOPLE),
        at_position=1,
    )
    factory.create(at_position=2)
    factory.create(at_position=3)
    factory.create(at_position=4)

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].thumbnail_id == largest_detection.id


def test_should_select_highest_score_as_best(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository, detection_repository=this_context.detection_repository
    )
    factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    factory.create(at_position=0)
    factory.create(at_position=1)
    best_detection = factory.create(
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25, confidence=1, label=ClassLabel.PEOPLE),
        at_position=2,
    )
    factory.create(
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25, confidence=0.99, label=ClassLabel.PEOPLE),
        at_position=3,
    )
    factory.create(at_position=4)

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].thumbnail_id == best_detection.id


def test_should_not_track_detections_from_wrong_video(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository, detection_repository=this_context.detection_repository
    )
    factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    factory.create(at_position=0)
    factory.create(at_position=1)
    factory.create(at_position=2)
    factory.create(at_position=3)
    factory.create(at_position=4)

    factory.with_video(UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b"))

    factory.create(at_position=0)
    factory.create(at_position=1)
    factory.create(at_position=2)
    factory.create(at_position=3)
    factory.create(at_position=4)

    # When
    this_context.use_case.execute(video_id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b"))

    # Then
    first_tracks = this_context.track_repository.list_video_tracks(
        video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")
    )
    assert len(first_tracks) == 0

    second_tracks = this_context.track_repository.list_video_tracks(
        video_id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b")
    )
    assert len(second_tracks) == 1


def test_should_not_track_on_empty_detections(this_context: ThisContext):
    # Given

    # When
    this_context.use_case.execute(video_id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b"))
    assert len(tracks) == 0
