from uuid import UUID

from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase


def test_should_remove_track_with_fewer_than_5_detections():
    # Given
    track_repository = InMemoryTrackRepository()
    use_case = TrackObjectsUseCase()

    # When
    use_case.execute(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))

    # Then
    assert track_repository.list_video_tracks(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")) == []
