from uuid import UUID

from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.track import Track
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase


class FakeTracker(Tracker):
    """Implement a fake tracker for testing purpose."""

    def __init__(self):
        self._tracks: list[Track] = []

    def track(self) -> list[Track]:
        """Return the saved tracks."""
        return self._tracks

    def add(self, track: Track) -> None:
        """Store a new track."""
        self._tracks.append(track)


def test_should_remove_track_with_fewer_than_5_detections():
    # Given
    tracker = FakeTracker()
    track_repository = InMemoryTrackRepository()
    use_case = TrackObjectsUseCase(
        track_repository=track_repository,
        tracker=tracker,
    )

    tracker.add(
        Track(
            id=UUID("5c22ec7e-f7e8-4488-b295-ea90bfca7b58"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            detections=[
                UUID("71a33805-2772-40b2-a1ca-b2ba66927603"),
                UUID("6380d673-457d-476c-9682-c6fbbfffdea4"),
                UUID("657f849a-a00a-41d2-b8df-7deb8ab00475"),
                UUID("f15b4db3-43fa-42c0-a453-7f66829d044e"),
            ],
        )
    )

    # When
    use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    assert track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")) == []


def test_should_track_an_object_appearing_more_than_5_times():
    # Given
    tracker = FakeTracker()
    track_repository = InMemoryTrackRepository()
    use_case = TrackObjectsUseCase(
        track_repository=track_repository,
        tracker=tracker,
    )

    tracker.add(
        Track(
            id=UUID("5c22ec7e-f7e8-4488-b295-ea90bfca7b58"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            detections=[
                UUID("71a33805-2772-40b2-a1ca-b2ba66927603"),
                UUID("6380d673-457d-476c-9682-c6fbbfffdea4"),
                UUID("657f849a-a00a-41d2-b8df-7deb8ab00475"),
                UUID("f15b4db3-43fa-42c0-a453-7f66829d044e"),
                UUID("2dfc4687-e126-4501-af0f-bdacbd5f0116"),
            ],
        )
    )

    # When
    use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    assert track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")) == [
        Track(
            id=UUID("5c22ec7e-f7e8-4488-b295-ea90bfca7b58"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            detections=[
                UUID("71a33805-2772-40b2-a1ca-b2ba66927603"),
                UUID("6380d673-457d-476c-9682-c6fbbfffdea4"),
                UUID("657f849a-a00a-41d2-b8df-7deb8ab00475"),
                UUID("f15b4db3-43fa-42c0-a453-7f66829d044e"),
                UUID("2dfc4687-e126-4501-af0f-bdacbd5f0116"),
            ],
        )
    ]
