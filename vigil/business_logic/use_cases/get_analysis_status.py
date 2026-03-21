from dataclasses import dataclass
from uuid import UUID

from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.video_repository import VideoRepository


@dataclass(frozen=True)
class AnalysisStatus:
    """Progress report for a video analysis job."""

    analysed_frames: int
    """Number of frames processed so far."""

    total_frames: int
    """Total number of frames in the video."""


class GetAnalysisStatusUseCase:
    """Return the progress of a video analysis job."""

    def __init__(self, frame_repository: FrameRepository, video_repository: VideoRepository) -> None:
        self._frame_repository = frame_repository
        self._video_repository = video_repository

    def execute(self, video_id: UUID) -> AnalysisStatus:
        """Return how many frames have been analysed out of the total."""
        frames = self._frame_repository.get_by_video_id(video_id)
        return AnalysisStatus(
            analysed_frames=len(frames),
            total_frames=self._video_repository.frame_count(video_id),
        )
