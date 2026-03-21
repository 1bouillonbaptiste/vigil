from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

import numpy as np
import numpy.typing as npt
import pytest

from vigil.business_logic.gateways.video_repository import VideoRepository
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.id_factory import IdFactory
from vigil.business_logic.use_cases.save_video import SaveVideoUseCase


class SpyVideoRepository(VideoRepository):
    """Records save calls for assertions."""

    def __init__(self) -> None:
        self.saved: list[tuple[VideoSource, bytes]] = []

    def save(self, source: VideoSource, data: bytes) -> None:
        self.saved.append((source, data))

    def read(self, video_id: UUID) -> Iterable[npt.NDArray[np.uint8]]:
        return []

    def frame_count(self, video_id: UUID) -> int:
        return 0


@dataclass
class ThisContext:
    """Context for testing save video use case."""

    repository: SpyVideoRepository
    use_case: SaveVideoUseCase


@pytest.fixture
def this_context() -> ThisContext:
    repository = SpyVideoRepository()
    use_case = SaveVideoUseCase(video_repository=repository)
    return ThisContext(repository=repository, use_case=use_case)


def test_should_return_video_id_derived_from_source(this_context: ThisContext) -> None:
    # Given
    source = VideoSource(uri="my_video.mp4")
    expected_id = IdFactory.new_video_id(source)

    # When
    video_id = this_context.use_case.execute(source=source, data=b"fake-bytes")

    # Then
    assert video_id == expected_id


def test_should_delegate_persistence_to_repository(this_context: ThisContext) -> None:
    # Given
    source = VideoSource(uri="my_video.mp4")
    data = b"fake-bytes"

    # When
    this_context.use_case.execute(source=source, data=data)

    # Then
    assert this_context.repository.saved == [(source, data)]


def test_should_return_same_id_for_same_source(this_context: ThisContext) -> None:
    # Given
    source = VideoSource(uri="my_video.mp4")

    # When
    id_1 = this_context.use_case.execute(source=source, data=b"first-upload")
    id_2 = this_context.use_case.execute(source=source, data=b"second-upload")

    # Then
    assert id_1 == id_2
