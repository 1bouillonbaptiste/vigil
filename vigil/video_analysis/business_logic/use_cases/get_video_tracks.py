from uuid import UUID

from vigil.video_analysis.business_logic.gateways.track_repository import TrackRepository
from vigil.video_analysis.business_logic.models.track import Track


class GetVideoTracksUseCase:
    """Return all tracks produced for a given video."""

    def __init__(self, track_repository: TrackRepository) -> None:
        self._track_repository = track_repository

    def execute(self, video_id: UUID) -> list[Track]:
        """Return all tracks (open and closed) for the given video."""
        return self._track_repository.list_by_video_id(video_id)
