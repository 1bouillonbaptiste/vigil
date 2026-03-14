from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import BoundingBox, Detection
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase


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
    this_context.detection_repository.add(
        Detection(
            id=UUID("71a33805-2772-40b2-a1ca-b2ba66927603"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=0,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("6380d673-457d-476c-9682-c6fbbfffdea4"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=1,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("657f849a-a00a-41d2-b8df-7deb8ab00475"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=2,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("f15b4db3-43fa-42c0-a453-7f66829d044e"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=3,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    assert this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")) == []


def test_should_track_an_object_appearing_more_than_5_times_included(this_context: ThisContext):
    # Given
    this_context.detection_repository.add(
        Detection(
            id=UUID("71a33805-2772-40b2-a1ca-b2ba66927603"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=0,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("6380d673-457d-476c-9682-c6fbbfffdea4"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=1,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("657f849a-a00a-41d2-b8df-7deb8ab00475"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=2,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("f15b4db3-43fa-42c0-a453-7f66829d044e"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=3,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("2dfc4687-e126-4501-af0f-bdacbd5f0116"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=4,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),
            confidence=1,
        )
    )

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].video_id == UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")
    assert tracks[0].detections == [
        UUID("71a33805-2772-40b2-a1ca-b2ba66927603"),
        UUID("6380d673-457d-476c-9682-c6fbbfffdea4"),
        UUID("657f849a-a00a-41d2-b8df-7deb8ab00475"),
        UUID("f15b4db3-43fa-42c0-a453-7f66829d044e"),
        UUID("2dfc4687-e126-4501-af0f-bdacbd5f0116"),
    ]


def test_should_select_largest_detection_as_best_on_same_confidence(this_context: ThisContext):
    # Given
    this_context.detection_repository.add(
        Detection(
            id=UUID("71a33805-2772-40b2-a1ca-b2ba66927603"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=0,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("6380d673-457d-476c-9682-c6fbbfffdea4"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=1,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30),  # largest bbox
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("657f849a-a00a-41d2-b8df-7deb8ab00475"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=2,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("f15b4db3-43fa-42c0-a453-7f66829d044e"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=3,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25),
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("2dfc4687-e126-4501-af0f-bdacbd5f0116"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=4,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25),
            confidence=1,
        )
    )

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].thumbnail_id == UUID("6380d673-457d-476c-9682-c6fbbfffdea4")


def test_should_select_highest_score_as_best(this_context: ThisContext):
    # Given
    this_context.detection_repository.add(
        Detection(
            id=UUID("71a33805-2772-40b2-a1ca-b2ba66927603"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=0,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25),
            confidence=0.5,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("6380d673-457d-476c-9682-c6fbbfffdea4"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=1,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25),
            confidence=0.5,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("657f849a-a00a-41d2-b8df-7deb8ab00475"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=2,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=20),  # smaller bbox but higher confidence
            confidence=1,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("f15b4db3-43fa-42c0-a453-7f66829d044e"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=3,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25),
            confidence=0.5,
        )
    )
    this_context.detection_repository.add(
        Detection(
            id=UUID("2dfc4687-e126-4501-af0f-bdacbd5f0116"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            frame_index=4,
            bbox=BoundingBox(center_x=100, center_y=50, width=10, height=25),
            confidence=0.5,
        )
    )

    # When
    this_context.use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    tracks = this_context.track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    assert len(tracks) == 1
    assert tracks[0].thumbnail_id == UUID("657f849a-a00a-41d2-b8df-7deb8ab00475")
