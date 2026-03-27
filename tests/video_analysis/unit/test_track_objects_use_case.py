from dataclasses import dataclass

import pytest

from vigil.video_analysis.adapters.secondary.fake_tracker import FakeTracker
from vigil.video_analysis.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.video_analysis.business_logic.models.detection import BoundingBox, ClassLabel, Detection, Prediction
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.id_factory import IdFactory
from vigil.video_analysis.business_logic.use_cases.track_objects import TrackObjectsUseCase

VIDEO_ID = IdFactory.new_video_id(VideoSource(uri="test-video"))

_FRAME_ID_0 = IdFactory.new_frame_id(video_id=VIDEO_ID, position=0)
_FRAME_ID_1 = IdFactory.new_frame_id(video_id=VIDEO_ID, position=1)

_BBOX = BoundingBox(center_x=10, center_y=10, width=5, height=5)

_DETECTION_0 = Detection(
    frame_id=_FRAME_ID_0,
    frame_position=0,
    prediction=Prediction(bbox=_BBOX, confidence=0.9, label=ClassLabel.PERSON),
)
_DETECTION_1 = Detection(
    frame_id=_FRAME_ID_1,
    frame_position=1,
    prediction=Prediction(bbox=_BBOX, confidence=0.9, label=ClassLabel.PERSON),
)


@dataclass
class ThisContext:
    track_repository: InMemoryTrackRepository
    use_case: TrackObjectsUseCase


@pytest.fixture
def this_context() -> ThisContext:
    track_repository = InMemoryTrackRepository()
    use_case = TrackObjectsUseCase(tracker=FakeTracker(), track_repository=track_repository)
    return ThisContext(track_repository=track_repository, use_case=use_case)


def test_should_match_instance_across_several_frames(this_context: ThisContext) -> None:
    this_context.use_case.execute(video_id=VIDEO_ID, detections=[_DETECTION_0, _DETECTION_1])

    tracks = this_context.track_repository.list_by_video_id(VIDEO_ID)
    assert len(tracks) == 1
    assert tracks[0].detections == (_DETECTION_0, _DETECTION_1)
