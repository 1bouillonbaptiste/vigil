from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.shared_kernel.models.image import Image
from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.models.video_created import VideoCreated
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.id_factory import IdFactory
from vigil.video_analysis.business_logic.use_cases.save_video import SaveVideoUseCase

TOTAL_FRAMES = 42


class SpyVideoRepository(VideoRepository):
    """Records save calls for assertions."""

    def __init__(self) -> None:
        self.saved: list[tuple[VideoSource, bytes]] = []

    def save(self, source: VideoSource, data: bytes) -> None:
        self.saved.append((source, data))

    def read(self, video_id: UUID) -> Iterable[Image]:
        return []

    def frame_count(self, video_id: UUID) -> int:
        return TOTAL_FRAMES


@dataclass
class ThisContext:
    """Context for testing save video use case."""

    repository: SpyVideoRepository
    publisher: InMemoryEventPublisher
    use_case: SaveVideoUseCase


@pytest.fixture
def this_context() -> ThisContext:
    repository = SpyVideoRepository()
    publisher = InMemoryEventPublisher()
    use_case = SaveVideoUseCase(video_repository=repository, domain_event_publisher=publisher)
    return ThisContext(repository=repository, publisher=publisher, use_case=use_case)


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


def test_should_publish_video_created_event(this_context: ThisContext) -> None:
    # Given
    source = VideoSource(uri="my_video.mp4")
    expected_video_id = IdFactory.new_video_id(source)
    published: list[VideoCreated] = []

    def capture(event: VideoCreated) -> None:
        published.append(event)

    this_context.publisher.subscribe(capture)

    # When
    this_context.use_case.execute(source=source, data=b"fake-bytes")

    # Then
    assert published == [VideoCreated(video_id=expected_video_id, total_frames=TOTAL_FRAMES)]
