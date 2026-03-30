from uuid import UUID, uuid4

import numpy as np

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
    """Fake frame reader that returns a fixed 1x1 black image for any crop."""

    def read_crop(self, video_id: UUID, frame_position: int, bbox: BoundingBox) -> Image:
        return Image(np.zeros((1, 1, 3), dtype=np.uint8))


def test_should_index_a_new_track():
    # Given
    track_repository = InMemoryEmbeddedTrackRepository()
    model = FakeEmbeddingModel()
    use_case = IndexTrackUseCase(
        track_repository=track_repository,
        frame_reader=FakeFrameReader(),
        model=model,
    )
    detections = [
        DetectionRef(detection_id=DETECTION_ID, frame_position=0, bbox=BBOX),
        DetectionRef(detection_id=DETECTION_ID_2, frame_position=1, bbox=BBOX),
    ]

    # When
    use_case.execute(track_id=TRACK_ID, video_id=VIDEO_ID, detections=detections)

    # Then
    assert track_repository.list_tracks() == [
        EmbeddedTrack(id=TRACK_ID, detections=(Embedding((0.5, 0.5)), Embedding((0.5, 0.5)))),
    ]
