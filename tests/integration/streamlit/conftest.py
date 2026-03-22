from collections.abc import Callable, Generator
from dataclasses import replace
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
from starlette.testclient import TestClient

from vigil.adapters.primary.fastapi.app_dependencies import (
    _get_detection_model,
    _get_frame_repository,
    _get_track_repository,
    _get_tracker,
    _get_video_repository,
)
from vigil.adapters.primary.fastapi.main import app
from vigil.adapters.primary.streamlit.components.models import BoundingBox, DetectionData, TrackData
from vigil.adapters.secondary.fake_detection_model import FakeDetectionModel
from vigil.adapters.secondary.fake_tracker import FakeTracker
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.local_video_repository import LocalVideoRepository

_VIDEO_FRAMES = 10
_VIDEO_SIZE = (64, 64)


@pytest.fixture(scope="function")
def vigil_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    """TestClient wired with fake/in-memory infrastructure."""
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    frame_repository = InMemoryFrameRepository()
    track_repository = InMemoryTrackRepository()

    app.dependency_overrides[_get_video_repository] = lambda: video_repository
    app.dependency_overrides[_get_frame_repository] = lambda: frame_repository
    app.dependency_overrides[_get_track_repository] = lambda: track_repository
    app.dependency_overrides[_get_detection_model] = lambda: FakeDetectionModel()
    app.dependency_overrides[_get_tracker] = lambda: FakeTracker()

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


@pytest.fixture()
def make_detection() -> Callable[..., DetectionData]:
    """Factory for DetectionData with sensible defaults."""

    def _make(**overrides: Any) -> DetectionData:
        defaults = DetectionData(
            frame_position=0,
            label="person",
            confidence=0.9,
            bbox=BoundingBox(center_x=32, center_y=32, width=20, height=20),
        )
        return replace(defaults, **overrides)

    return _make


@pytest.fixture()
def make_track(make_detection: Callable[..., DetectionData]) -> Callable[..., TrackData]:
    """Factory for TrackData with sensible defaults."""

    def _make(**overrides: Any) -> TrackData:
        defaults = TrackData(id="track-1", closed=True, detections=(make_detection(),))
        return replace(defaults, **overrides)

    return _make
