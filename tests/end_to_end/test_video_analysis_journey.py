from dataclasses import dataclass
from pathlib import Path

import pytest

from vigil.adapters.secondary.fake_tracker import FakeTracker
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.adapters.secondary.yolo_detection_model import make_yolo_detection_model
from vigil.business_logic.models.detection import ClassLabel
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.detection_service import DetectionService
from vigil.business_logic.use_cases.get_video_tracks import GetVideoTracksUseCase
from vigil.business_logic.use_cases.save_video import SaveVideoUseCase
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase
from vigil.business_logic.use_cases.video_analysis_workflow import VideoAnalysisWorkflow

_FIXTURE_VIDEO: Path = Path(__file__).parent / "fixtures" / "people_10frames.mp4"


@dataclass
class ThisContext:
    save_video: SaveVideoUseCase
    analyze_video: VideoAnalysisWorkflow
    get_video_tracks: GetVideoTracksUseCase


@pytest.fixture(scope="module")
def this_context(tmp_path_factory: pytest.TempPathFactory) -> ThisContext:
    storage = tmp_path_factory.mktemp("journey")
    video_repository = LocalVideoRepository(storage_dir=storage)
    frame_repository = InMemoryFrameRepository()
    track_repository = InMemoryTrackRepository()
    detection_model = make_yolo_detection_model(model_name="yolov8n")
    detection_service = DetectionService(model=detection_model)
    track_use_case = TrackObjectsUseCase(track_repository=track_repository, tracker=FakeTracker())

    return ThisContext(
        save_video=SaveVideoUseCase(video_repository=video_repository),
        analyze_video=VideoAnalysisWorkflow(
            video_repository=video_repository,
            frame_repository=frame_repository,
            detection_service=detection_service,
            track_use_case=track_use_case,
            batch_size=8,
        ),
        get_video_tracks=GetVideoTracksUseCase(track_repository=track_repository),
    )


def test_should_detect_people_across_video_frames(this_context: ThisContext) -> None:
    video_id = this_context.save_video.execute(
        source=VideoSource(uri="people_10frames.mp4"),
        data=_FIXTURE_VIDEO.read_bytes(),
    )

    this_context.analyze_video.execute(video_id=video_id)

    tracks = this_context.get_video_tracks.execute(video_id=video_id)
    labels = {detection.prediction.label for track in tracks for detection in track.detections}
    assert ClassLabel.PERSON in labels
