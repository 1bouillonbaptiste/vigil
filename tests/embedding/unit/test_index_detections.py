from dataclasses import dataclass
from uuid import UUID, uuid4

import numpy as np
import pytest

from vigil.embedding.adapters.secondary.fake_embedding_model import FakeEmbeddingModel
from vigil.embedding.adapters.secondary.in_memory_embedded_track_repository import InMemoryEmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.frame_reader import FrameReader
from vigil.embedding.business_logic.models.detection_ref import DetectionRef
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack, Embedding
from vigil.embedding.business_logic.use_cases.index_track import IndexTrackUseCase
from vigil.shared_kernel.models.bounding_box import BoundingBox
from vigil.shared_kernel.models.image import Image

TRACK_ID = uuid4()
VIDEO_ID = uuid4()
DETECTION_ID = uuid4()
DETECTION_ID_2 = uuid4()
BBOX = BoundingBox(center_x=10, center_y=10, width=5, height=5)


class FakeFrameReader(FrameReader):
    """Fake frame reader that returns a fixed 1x1 black image and records
    requested positions."""

    def __init__(self) -> None:
        self.read_positions: list[int] = []

    def read_crop(self, video_id: UUID, frame_position: int, bbox: BoundingBox) -> Image:
        self.read_positions.append(frame_position)
        return Image(np.zeros((1, 1, 3), dtype=np.uint8))


def make_detections(count: int) -> list[DetectionRef]:
    return [DetectionRef(detection_id=uuid4(), frame_position=i, bbox=BBOX) for i in range(count)]


@dataclass
class ThisContext:
    repository: InMemoryEmbeddedTrackRepository
    frame_reader: FakeFrameReader
    use_case: IndexTrackUseCase


@pytest.fixture(scope="function")
def this_context() -> ThisContext:
    repository = InMemoryEmbeddedTrackRepository()
    frame_reader = FakeFrameReader()
    return ThisContext(
        repository=repository,
        frame_reader=frame_reader,
        use_case=IndexTrackUseCase(
            track_repository=repository,
            frame_reader=frame_reader,
            model=FakeEmbeddingModel(),
        ),
    )


def test_should_index_a_new_track(this_context: ThisContext):
    # Given
    detections = [
        DetectionRef(detection_id=DETECTION_ID, frame_position=0, bbox=BBOX),
        DetectionRef(detection_id=DETECTION_ID_2, frame_position=1, bbox=BBOX),
    ]

    # When
    this_context.use_case.execute(track_id=TRACK_ID, video_id=VIDEO_ID, detections=detections)

    # Then
    assert this_context.repository.list_tracks() == [
        EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)), Embedding((0.5, 0.5)))),
    ]


def test_should_sample_evenly_spaced_detections(this_context: ThisContext):
    # When
    this_context.use_case.execute(track_id=TRACK_ID, video_id=VIDEO_ID, detections=make_detections(10))

    # Then - evenly spaced: indices 0, 2, 4, 6, 9 out of 10
    assert this_context.frame_reader.read_positions == [0, 2, 4, 6, 9]
