from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import BoundingBox, Detection
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase

from tests.helpers import DetectionFactory


class FakeTracker(Tracker):
    """Fake tracker for testing purpose.

    This fake creates a single track given detections.
    Raises an error if several detections appear in the same frame.
    """

    def track(self, detections: list[Detection]) -> list[list[Detection]]:
        """Return the saved tracks."""
        tracked_frames: list[int] = [detection.frame_index for detection in detections]
        if len(tracked_frames) != len(set(tracked_frames)):
            raise RuntimeError("Found multiple detections in the same frame, not yet supported.")

        return [sorted(detections, key=lambda d: d.frame_index)]


@dataclass
class ThisContext:
    """Testing context for `TrackObjectsUseCase`."""

    detection_repository: InMemoryDetectionRepository
    tracker: FakeTracker
    track_repository: InMemoryTrackRepository
    use_case: TrackObjectsUseCase


@pytest.fixture
def this_context() -> ThisContext:
    detection_repository = InMemoryDetectionRepository()
    tracker = FakeTracker()
    track_repository = InMemoryTrackRepository()
    use_case = TrackObjectsUseCase(
        detection_repository=detection_repository,
        tracker=tracker,
        track_repository=track_repository,
    )
    return ThisContext(
        detection_repository=detection_repository,
        tracker=tracker,
        track_repository=track_repository,
        use_case=use_case,
    )


def test_should_remove_track_with_fewer_than_5_detections(this_context: ThisContext):
    # Given
    factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")) == []


def test_should_track_an_object_appearing_more_than_5_times_included(this_context: ThisContext):
    # Given
    factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].video_id == UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")
    assert len(tracks[0].detections) == 5


def test_should_select_largest_detection_as_best_on_same_confidence(this_context: ThisContext):
    # Given
    factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    this_context.detection_repository.add(factory.create())
    largest_detection = factory.create(bbox=BoundingBox(center_x=100, center_y=50, width=10, height=35))
    this_context.detection_repository.add(largest_detection)
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].thumbnail_id == largest_detection.id


def test_should_select_highest_score_as_best(this_context: ThisContext):
    # Given
    factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())
    best_detection = factory.create(bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25), confidence=1)
    this_context.detection_repository.add(best_detection)
    this_context.detection_repository.add(factory.create())
    this_context.detection_repository.add(factory.create())

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].thumbnail_id == best_detection.id


def test_should_not_track_detections_from_wrong_video(this_context: ThisContext):
    # Given
    first_factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    this_context.detection_repository.add(first_factory.create())
    this_context.detection_repository.add(first_factory.create())
    this_context.detection_repository.add(first_factory.create())
    this_context.detection_repository.add(first_factory.create())
    this_context.detection_repository.add(first_factory.create())

    second_factory = DetectionFactory(video_id=UUID("6f7f36e7-c0c8-4679-b3c3-835fc20ca59b"))
    this_context.detection_repository.add(second_factory.create())
    this_context.detection_repository.add(second_factory.create())
    this_context.detection_repository.add(second_factory.create())
    this_context.detection_repository.add(second_factory.create())
    this_context.detection_repository.add(second_factory.create())

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
