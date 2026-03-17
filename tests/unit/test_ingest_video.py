from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pytest

from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_frame_store import InMemoryFrameStore
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.frame import FrameData
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.use_cases.ingest_video import IngestVideoUseCase


class StubVideoReader(VideoReader):
    """Stub video reader implementation."""

    def __init__(self):
        self._frames: list[FrameData] = []

    def add(self, frame: FrameData) -> None:
        """Insert a new video frame in the collection."""
        self._frames.append(frame)

    def read(self, source: VideoSource) -> Iterable[FrameData]:
        """Yields controlled frames."""
        return self._frames


@dataclass
class ThisContext:
    """Context manager for the video ingestion use case."""

    video_reader: StubVideoReader
    frame_store: InMemoryFrameStore
    frame_repository: InMemoryFrameRepository
    use_case: IngestVideoUseCase


@pytest.fixture(scope="function")
def this_context() -> ThisContext:
    video_reader = StubVideoReader()
    frame_store = InMemoryFrameStore()
    frame_repository = InMemoryFrameRepository()
    use_case = IngestVideoUseCase(
        video_reader=video_reader,
        frame_store=frame_store,
        frame_repository=frame_repository,
    )
    return ThisContext(
        video_reader=video_reader,
        frame_store=frame_store,
        frame_repository=frame_repository,
        use_case=use_case,
    )


def test_should_store_video_as_frames(this_context: ThisContext):
    # Given
    this_context.video_reader.add(
        FrameData(
            data=np.array([1, 0], dtype=np.uint8),
        )
    )
    this_context.video_reader.add(
        FrameData(
            data=np.array([0, 1], dtype=np.uint8),
        )
    )

    # When
    source = VideoSource(uri="foo")
    this_context.use_case.execute(source=source)

    # Then
    frames = this_context.frame_repository.get_by_video_id(source.video_id)
    for frame in frames:
        # Frames where created to be a one hot vector with 1 at frame's position in the video
        assert this_context.frame_store.load(frame).data.argmax() == frame.position
