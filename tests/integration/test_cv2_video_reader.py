"""Integration tests for Cv2VideoReader.

Requires opencv-python-headless to be installed.
"""

import cv2
import numpy as np
import pytest

from vigil.adapters.secondary.cv2_video_reader import Cv2VideoReader
from vigil.business_logic.gateways.video_reader import VideoDurationExceededError
from vigil.business_logic.models.raw_frame import RawFrame


@pytest.fixture
def short_video(tmp_path):
    """Synthetic 3-second video at 10 fps (30 frames, 320x240)."""
    path = str(tmp_path / "test.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, 10, (320, 240))
    for i in range(30):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        frame[:, :, 0] = i * 8  # vary blue channel so frames differ
        writer.write(frame)
    writer.release()
    return path


@pytest.fixture
def long_video(tmp_path):
    """Synthetic video just over 5 minutes (10 fps, 3010 frames)."""
    path = str(tmp_path / "long.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, 10, (64, 64))
    blank = np.zeros((64, 64, 3), dtype=np.uint8)
    for _ in range(3010):
        writer.write(blank)
    writer.release()
    return path


@pytest.mark.integration
def test_reader_yields_raw_frames(short_video):
    reader = Cv2VideoReader()
    frames = list(reader.read(short_video, frame_interval=1))

    assert len(frames) == 30
    assert all(isinstance(f, RawFrame) for f in frames)
    assert all(isinstance(f.data, bytes) and len(f.data) > 0 for f in frames)


@pytest.mark.integration
def test_frame_interval_reduces_yielded_count(short_video):
    reader = Cv2VideoReader()
    frames = list(reader.read(short_video, frame_interval=5))

    assert len(frames) == 6  # frames at indices 0, 5, 10, 15, 20, 25


@pytest.mark.integration
def test_frame_index_reflects_source_position(short_video):
    reader = Cv2VideoReader()
    frames = list(reader.read(short_video, frame_interval=5))

    assert [f.index for f in frames] == [0, 5, 10, 15, 20, 25]


@pytest.mark.integration
def test_raises_file_not_found_for_missing_video():
    reader = Cv2VideoReader()
    with pytest.raises(FileNotFoundError):
        list(reader.read("/nonexistent/video.mp4", frame_interval=1))


@pytest.mark.integration
def test_raises_duration_exceeded_for_long_video(long_video):
    reader = Cv2VideoReader()
    with pytest.raises(VideoDurationExceededError):
        list(reader.read(long_video, frame_interval=1))
