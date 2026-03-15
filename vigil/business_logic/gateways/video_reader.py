from typing import Iterator, Protocol

from vigil.business_logic.models.raw_frame import RawFrame


class VideoDurationExceededError(Exception):
    """Raised when a submitted video exceeds the maximum supported duration."""


class VideoReader(Protocol):
    """Interface for iterating over frames from a recorded video file."""

    def read(self, video_path: str, frame_interval: int) -> Iterator[RawFrame]:
        """Yield sampled frames from the video at the given path.

        Args:
            video_path: Absolute path to the video file.
            frame_interval: Yield one frame every N frames (e.g. 5 yields every 5th).

        Raises:
            FileNotFoundError: If the video file cannot be opened.
            VideoDurationExceededError: If the video exceeds the 5-minute limit.
        """
        ...
