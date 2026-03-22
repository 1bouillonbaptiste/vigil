from pathlib import Path

from starlette.testclient import TestClient

from vigil.adapters.primary.fastapi.app_dependencies import (
    _get_detection_model,
    _get_frame_repository,
    _get_track_repository,
    _get_tracker,
    _get_video_repository,
)
from vigil.adapters.secondary.fake_detection_model import FakeDetectionModel
from vigil.adapters.secondary.fake_tracker import FakeTracker
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.id_factory import IdFactory


def test_can_save_a_video(fastapi_client: TestClient, tmp_path: Path, video_filepath: Path):
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    frame_repository = InMemoryFrameRepository()
    detection_model = FakeDetectionModel()
    track_repository = InMemoryTrackRepository()
    tracker = FakeTracker()

    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: video_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_frame_repository] = lambda: frame_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_track_repository] = lambda: track_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_detection_model] = lambda: detection_model  # type: ignore
    fastapi_client.app.dependency_overrides[_get_tracker] = lambda: tracker  # type: ignore

    with open(video_filepath, "rb") as file:
        response = fastapi_client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    assert response.status_code == 202
    expected_video_id = IdFactory.new_video_id(VideoSource(uri="video.mp4"))
    assert response.json() == {"video_id": str(expected_video_id)}


def test_analysis_saves_tracks_in_repository(fastapi_client: TestClient, tmp_path: Path, video_filepath: Path):
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    frame_repository = InMemoryFrameRepository()
    detection_model = FakeDetectionModel()
    track_repository = InMemoryTrackRepository()
    tracker = FakeTracker()

    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: video_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_frame_repository] = lambda: frame_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_track_repository] = lambda: track_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_detection_model] = lambda: detection_model  # type: ignore
    fastapi_client.app.dependency_overrides[_get_tracker] = lambda: tracker  # type: ignore

    with open(video_filepath, "rb") as file:
        fastapi_client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    assert len(track_repository.list_all()) == 1
