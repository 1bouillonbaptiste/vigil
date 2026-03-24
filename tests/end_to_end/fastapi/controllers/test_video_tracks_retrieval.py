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


def test_can_get_video_tracks(fastapi_client: TestClient, tmp_path: Path, fake_video_filepath: Path):
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

    with open(fake_video_filepath, "rb") as file:
        post_response = fastapi_client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    video_id = post_response.json()["video_id"]
    response = fastapi_client.get(f"/videos/{video_id}/tracks")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert len(body["tracks"]) == 1
    assert len(body["tracks"][0]["detections"]) == 10
