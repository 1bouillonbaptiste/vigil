from uuid import UUID

from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.models.track import Track


def test_can_save_and_load_track():
    track = Track(
        id=UUID("6609e565-100b-4f23-8f4e-9d7f92a8faf7"),
        video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
        detections=[
            UUID("cc9f9ad9-e498-4e19-bc5d-ba2324fac4c4"),
            UUID("1741a55d-40f9-4916-8fa6-347244ce6409"),
            UUID("7b79d155-d17a-40a3-89cf-7a5c76673a10"),
        ],
        thumbnail_id=UUID("cc9f9ad9-e498-4e19-bc5d-ba2324fac4c4"),
    )

    repo = InMemoryTrackRepository()
    repo.save(track)

    result = repo.get_by_id(UUID("6609e565-100b-4f23-8f4e-9d7f92a8faf7"))

    assert result == track
