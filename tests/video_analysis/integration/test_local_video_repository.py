from pathlib import Path

import cv2
import numpy as np
import pytest

from vigil.shared_kernel.models.bounding_box import BoundingBox
from vigil.shared_kernel.models.image import Image
from vigil.video_analysis.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.video_analysis.business_logic.exceptions import VideoNotFoundError
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.id_factory import IdFactory


@pytest.fixture(scope="function")
def fake_video_filepath(tmp_path: Path) -> Path:
    """Write a minimal MP4 video to disk for testing."""
    filepath = tmp_path / "video.mp4"
    writer = cv2.VideoWriter(
        filepath.as_posix(),
        cv2.VideoWriter.fourcc(*"mp4v"),
        fps=25,
        frameSize=(64, 64),
    )
    n_frames = 10
    for i in range(n_frames):
        frame = np.full((64, 64, 3), i * 25, dtype=np.uint8)
        writer.write(frame)
    writer.release()

    return filepath


@pytest.fixture(scope="function")
def repository(tmp_path: Path) -> LocalVideoRepository:
    return LocalVideoRepository(storage_dir=tmp_path)


def test_should_save_and_read_back_correct_frame_count(
    repository: LocalVideoRepository,
    fake_video_filepath: Path,
) -> None:
    source = VideoSource(uri="clip.mp4")
    repository.save(source, fake_video_filepath.read_bytes())
    video_id = IdFactory.new_video_id(source)

    frames = list(repository.read(video_id))

    assert len(frames) == 10


def test_should_report_correct_frame_count(
    repository: LocalVideoRepository,
    fake_video_filepath: Path,
) -> None:
    source = VideoSource(uri="clip.mp4")
    repository.save(source, fake_video_filepath.read_bytes())
    video_id = IdFactory.new_video_id(source)

    assert repository.frame_count(video_id) == 10


def test_read_raises_video_not_found_for_unknown_id(repository: LocalVideoRepository) -> None:
    with pytest.raises(VideoNotFoundError):
        list(repository.read(IdFactory.new_video_id(VideoSource(uri="unknown.mp4"))))


def test_frame_count_raises_video_not_found_for_unknown_id(repository: LocalVideoRepository) -> None:
    with pytest.raises(VideoNotFoundError):
        repository.frame_count(IdFactory.new_video_id(VideoSource(uri="unknown.mp4")))


def test_read_crop_should_expand_bbox_uniformly_using_10_percent_of_largest_side(
    repository: LocalVideoRepository,
    fake_video_filepath: Path,
) -> None:
    source = VideoSource(uri="clip.mp4")
    repository.save(source, fake_video_filepath.read_bytes())
    video_id = IdFactory.new_video_id(source)
    # thin bbox: 10 wide x 40 tall, centered at (32, 32)
    # margin = 10% of max(10, 40) = 4px per side -> 18x48
    bbox = BoundingBox(center_x=32, center_y=32, width=10, height=40)

    crop = repository.read_crop(video_id, frame_position=0, bbox=bbox)

    assert crop.numpy().shape == (48, 18, 3)


def test_should_yield_numpy_arrays(
    repository: LocalVideoRepository,
    fake_video_filepath: Path,
) -> None:
    source = VideoSource(uri="clip.mp4")
    repository.save(source, fake_video_filepath.read_bytes())
    video_id = IdFactory.new_video_id(source)

    frames = list(repository.read(video_id))

    assert all(isinstance(f, Image) for f in frames)
