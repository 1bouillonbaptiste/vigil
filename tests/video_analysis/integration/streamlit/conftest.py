from collections.abc import Generator
from pathlib import Path

import cv2
import numpy as np
import pytest
from starlette.testclient import TestClient

from vigil.app.fastapi.main import app
from vigil.monitoring.adapters.primary.events_subscriber.frame_detected_subscriber import FrameDetectedSubscriber
from vigil.monitoring.adapters.primary.events_subscriber.video_created_subscriber import VideoCreatedSubscriber
from vigil.monitoring.adapters.secondary.in_memory_analysis_job_repository import InMemoryAnalysisJobRepository
from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.video_analysis.adapters.primary.fastapi.app_dependencies import (
    _get_analysis_job_repository,
    _get_detection_model,
    _get_domain_event_publisher,
    _get_track_repository,
    _get_tracker,
    _get_video_repository,
)
from vigil.video_analysis.adapters.secondary.fake_detection_model import FakeDetectionModel
from vigil.video_analysis.adapters.secondary.fake_tracker import FakeTracker
from vigil.video_analysis.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.video_analysis.adapters.secondary.local_video_repository import LocalVideoRepository

_VIDEO_FRAMES = 10
_VIDEO_SIZE = (64, 64)


@pytest.fixture(scope="function")
def vigil_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    """TestClient wired with fake/in-memory infrastructure."""
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    track_repository = InMemoryTrackRepository()
    domain_event_publisher = InMemoryEventPublisher()
    analysis_job_repository = InMemoryAnalysisJobRepository()

    VideoCreatedSubscriber(publisher=domain_event_publisher, repository=analysis_job_repository).subscribe()
    FrameDetectedSubscriber(publisher=domain_event_publisher, repository=analysis_job_repository).subscribe()

    app.dependency_overrides[_get_video_repository] = lambda: video_repository
    app.dependency_overrides[_get_track_repository] = lambda: track_repository
    app.dependency_overrides[_get_detection_model] = lambda: FakeDetectionModel()
    app.dependency_overrides[_get_tracker] = lambda: FakeTracker()
    app.dependency_overrides[_get_analysis_job_repository] = lambda: analysis_job_repository
    app.dependency_overrides[_get_domain_event_publisher] = lambda: domain_event_publisher

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def video_path(tmp_path: Path) -> Path:
    """Minimal 10-frame 64x64 MP4 video written to a temp file."""
    filepath = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(
        filepath.as_posix(),
        cv2.VideoWriter.fourcc(*"mp4v"),
        fps=25,
        frameSize=_VIDEO_SIZE,
    )
    for i in range(_VIDEO_FRAMES):
        writer.write(np.full((*_VIDEO_SIZE[::-1], 3), i * 25, dtype=np.uint8))
    writer.release()
    return filepath


@pytest.fixture(scope="function")
def video_bytes(video_path: Path) -> bytes:
    """Minimal 10-frame 64x64 MP4 video as raw bytes."""
    return video_path.read_bytes()
