from collections.abc import Iterable
from uuid import UUID

from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.frame import VideoFrame
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.use_cases.ingest_video import IngestVideoUseCase


class StubVideoReader(VideoReader):
    """Stub video reader implementation."""

    def __init__(self, frames: Iterable[VideoFrame]):
        self._frames = frames

    def read(self, source: VideoSource) -> Iterable[VideoFrame]:
        """Yields controlled frames."""
        for frame in self._frames:
            yield frame


def test_should_store_video_as_frames():
    # Given
    frame_repository = InMemoryFrameRepository()
    video_reader = StubVideoReader(
        frames=[
            VideoFrame(
                id=UUID("feda891b-3899-478e-87f5-f5e814a0b800"),
                video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
                position=0,
            ),
            VideoFrame(
                id=UUID("feda891b-3899-478e-87f5-f5e814a0b801"),
                video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
                position=1,
            ),
        ]
    )
    use_case = IngestVideoUseCase(video_reader=video_reader, frame_repository=frame_repository)

    # When
    use_case.execute(source=VideoSource(uri="foo"))

    # Then
    expected = [
        VideoFrame(
            id=UUID("feda891b-3899-478e-87f5-f5e814a0b800"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            position=0,
        ),
        VideoFrame(
            id=UUID("feda891b-3899-478e-87f5-f5e814a0b801"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            position=1,
        ),
    ]
    assert frame_repository.get_by_video_id(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")) == expected
