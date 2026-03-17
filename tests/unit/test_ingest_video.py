from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.frame import VideoFrame
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.use_cases.ingest_video import IngestVideoUseCase


class StubVideoReader(VideoReader):
    """Stub video reader implementation."""

    def __init__(self):
        self._frames: list[VideoFrame] = []

    def add(self, frame: VideoFrame) -> None:
        """Insert a new video frame in the collection."""
        self._frames.append(frame)

    def read(self, source: VideoSource) -> Iterable[VideoFrame]:
        """Yields controlled frames."""
        return self._frames


@dataclass
class ThisContext:
    """Context manager for the video ingestion use case."""

    video_reader: StubVideoReader
    frame_repository: InMemoryFrameRepository
    use_case: IngestVideoUseCase


@pytest.fixture(scope="session")
def this_context() -> ThisContext:
    video_reader = StubVideoReader()
    frame_repository = InMemoryFrameRepository()
    use_case = IngestVideoUseCase(
        video_reader=video_reader,
        frame_repository=frame_repository,
    )
    return ThisContext(
        video_reader=video_reader,
        frame_repository=frame_repository,
        use_case=use_case,
    )


def test_should_store_video_as_frames(this_context: ThisContext):
    # Given
    this_context.video_reader.add(
        VideoFrame(
            id=UUID("feda891b-3899-478e-87f5-f5e814a0b800"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            position=0,
        )
    )
    this_context.video_reader.add(
        VideoFrame(
            id=UUID("feda891b-3899-478e-87f5-f5e814a0b801"),
            video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"),
            position=1,
        )
    )

    # When
    this_context.use_case.execute(source=VideoSource(uri="foo"))

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
    assert this_context.frame_repository.get_by_video_id(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")) == expected
