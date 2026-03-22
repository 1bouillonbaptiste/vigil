from pathlib import Path

import cv2
import numpy as np
import pytest
from starlette.testclient import TestClient

from vigil.adapters.primary.fastapi.main import app


@pytest.fixture
def fastapi_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def video_filepath(tmp_path: Path) -> Path:
    """Generate a 10-frame MP4 video in a temporary directory."""
    filepath = tmp_path / "video.mp4"
    writer = cv2.VideoWriter(
        filepath.as_posix(),
        cv2.VideoWriter.fourcc(*"mp4v"),
        fps=25,
        frameSize=(64, 64),
    )
    for i in range(10):
        writer.write(np.full((64, 64, 3), i * 25, dtype=np.uint8))
    writer.release()
    return filepath
