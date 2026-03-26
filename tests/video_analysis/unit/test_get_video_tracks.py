from uuid import UUID

import pytest

from vigil.video_analysis.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.video_analysis.business_logic.models.detection import BoundingBox, ClassLabel, Detection, Prediction
from vigil.video_analysis.business_logic.models.frame import FrameId
from vigil.video_analysis.business_logic.models.track import Track
from vigil.video_analysis.business_logic.services.id_factory import IdFactory
from vigil.video_analysis.business_logic.use_cases.get_video_tracks import GetVideoTracksUseCase

VIDEO_ID = UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")
OTHER_VIDEO_ID = UUID("ffffffff-0000-0000-0000-000000000000")
FRAME_ID = FrameId(UUID("8d672f18-906e-4ff9-a06d-938898683720"))


def _detection(bbox: BoundingBox) -> Detection:
    return Detection(
        frame_id=FRAME_ID,
        frame_position=0,
        prediction=Prediction(bbox=bbox, confidence=0.8, label=ClassLabel.PERSON),
    )


def _track(video_id: UUID, bbox: BoundingBox) -> Track:
    detection = _detection(bbox)
    return Track(
        id=IdFactory.new_track_id(detection),
        video_id=video_id,
        detections=(detection,),
    )


@pytest.fixture
def repository() -> InMemoryTrackRepository:
    return InMemoryTrackRepository()


def test_returns_empty_list_when_no_tracks(repository: InMemoryTrackRepository):
    use_case = GetVideoTracksUseCase(track_repository=repository)

    assert use_case.execute(video_id=VIDEO_ID) == []


def test_returns_all_tracks_for_video(repository: InMemoryTrackRepository):
    track = _track(VIDEO_ID, BoundingBox(1, 1, 1, 1))
    repository.save(track)

    use_case = GetVideoTracksUseCase(track_repository=repository)

    assert use_case.execute(video_id=VIDEO_ID) == [track]


def test_returns_multiple_tracks_for_same_video(repository: InMemoryTrackRepository):
    track_a = _track(VIDEO_ID, BoundingBox(1, 1, 1, 1))
    track_b = _track(VIDEO_ID, BoundingBox(2, 2, 2, 2))
    repository.save(track_a)
    repository.save(track_b)

    use_case = GetVideoTracksUseCase(track_repository=repository)

    result = use_case.execute(video_id=VIDEO_ID)
    assert len(result) == 2


def test_does_not_return_tracks_from_other_videos(repository: InMemoryTrackRepository):
    repository.save(_track(OTHER_VIDEO_ID, BoundingBox(1, 1, 1, 1)))

    use_case = GetVideoTracksUseCase(track_repository=repository)

    assert use_case.execute(video_id=VIDEO_ID) == []
