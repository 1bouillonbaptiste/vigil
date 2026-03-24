from dataclasses import dataclass
from pathlib import Path

import pytest
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


@dataclass
class ThisContext:
    """Context for testing vidoe analysis controller."""

    track_repository: InMemoryTrackRepository
    client: TestClient


@pytest.fixture(scope="function")
def this_context(fastapi_client: TestClient, tmp_path: Path) -> ThisContext:
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

    return ThisContext(track_repository=track_repository, client=fastapi_client)


def test_can_save_a_video(this_context: ThisContext, fake_video_filepath: Path):
    # When
    with open(fake_video_filepath, "rb") as file:
        response = this_context.client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    # Then
    assert response.status_code == 202
    expected_video_id = IdFactory.new_video_id(VideoSource(uri="video.mp4"))
    assert response.json() == {"video_id": str(expected_video_id)}


def test_analysis_saves_tracks_in_repository(this_context: ThisContext, fake_video_filepath: Path):
    # When
    with open(fake_video_filepath, "rb") as file:
        this_context.client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    # Then
    assert len(this_context.track_repository.list_all()) == 1
