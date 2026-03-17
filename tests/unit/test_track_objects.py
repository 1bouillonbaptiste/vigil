from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.iou_tracker import IouTracker
from vigil.business_logic.models.detection import BoundingBox, ClassLabel
from vigil.business_logic.models.track import Track
from vigil.business_logic.services.id_factory import IdFactory
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase

from tests.helpers import DetectionFactory

VIDEO_ID = UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")


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
    tracker = IouTracker(frame_repository=frame_repository)
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
    factory.with_video(VIDEO_ID)

    factory.create(at_position=0)
    factory.create(at_position=1)
    factory.create(at_position=2)
    factory.create(at_position=3)

    # When
    this_context.use_case.execute(video_id=VIDEO_ID)

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=VIDEO_ID) == []


def test_should_track_an_object_appearing_more_than_5_times_included(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository,
        detection_repository=this_context.detection_repository,
    )
    factory.with_video(VIDEO_ID)

    # Valid track with 5 detections
    d0 = factory.create(at_position=0)
    d1 = factory.create(at_position=1)
    d2 = factory.create(at_position=2)
    d3 = factory.create(at_position=3)
    d4 = factory.create(at_position=4)

    # Invalid track with 3 detections
    factory.create(at_position=8)
    factory.create(at_position=9)
    factory.create(at_position=10)

    # When
    this_context.use_case.execute(video_id=VIDEO_ID)

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=VIDEO_ID) == [
        Track(
            id=IdFactory.new_track_id(video_id=VIDEO_ID, detection_id=d0.id),
            video_id=VIDEO_ID,
            detections=[d0.id, d1.id, d2.id, d3.id, d4.id],
            thumbnail_id=d0.id,
        )
    ]


def test_should_select_largest_detection_as_best_on_same_confidence(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository, detection_repository=this_context.detection_repository
    )
    factory.with_video(VIDEO_ID)

    d0 = factory.create(at_position=0)
    largest_detection = factory.create(
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=35, confidence=0.8, label=ClassLabel.PEOPLE),
        at_position=1,
    )
    d2 = factory.create(at_position=2)
    d3 = factory.create(at_position=3)
    d4 = factory.create(at_position=4)

    # When
    this_context.use_case.execute(video_id=VIDEO_ID)

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=VIDEO_ID) == [
        Track(
            id=IdFactory.new_track_id(video_id=VIDEO_ID, detection_id=d0.id),
            video_id=VIDEO_ID,
            detections=[d0.id, largest_detection.id, d2.id, d3.id, d4.id],
            thumbnail_id=largest_detection.id,
        )
    ]


def test_should_select_highest_score_as_best(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository, detection_repository=this_context.detection_repository
    )
    factory.with_video(VIDEO_ID)

    d0 = factory.create(at_position=0)
    d1 = factory.create(at_position=1)
    best_detection = factory.create(
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25, confidence=1, label=ClassLabel.PEOPLE),
        at_position=2,
    )
    d3 = factory.create(
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25, confidence=0.99, label=ClassLabel.PEOPLE),
        at_position=3,
    )
    d4 = factory.create(at_position=4)

    # When
    this_context.use_case.execute(video_id=VIDEO_ID)

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=VIDEO_ID) == [
        Track(
            id=IdFactory.new_track_id(video_id=VIDEO_ID, detection_id=d0.id),
            video_id=VIDEO_ID,
            detections=[d0.id, d1.id, best_detection.id, d3.id, d4.id],
            thumbnail_id=best_detection.id,
        )
    ]


def test_should_not_track_detections_from_wrong_video(this_context: ThisContext):
    # Given
    factory = DetectionFactory(
        frame_repository=this_context.frame_repository, detection_repository=this_context.detection_repository
    )
    factory.with_video(VIDEO_ID)

    factory.create(at_position=0)
    factory.create(at_position=1)
    factory.create(at_position=2)
    factory.create(at_position=3)
    factory.create(at_position=4)

    # When
    this_context.use_case.execute(video_id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b"))

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=VIDEO_ID) == []


def test_should_not_track_on_empty_detections(this_context: ThisContext):
    # Given

    # When
    this_context.use_case.execute(video_id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b"))

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b")) == []
