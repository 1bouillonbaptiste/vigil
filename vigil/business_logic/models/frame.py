from dataclasses import dataclass
from uuid import UUID

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True)
class VideoFrame:
    """Represent a single frame from a video."""

    id: UUID
    """Frame unique identifier."""

    position: int
    """Ordering position of the frame in the video."""

    video_id: UUID
    """Video identifier the frame originally comes from."""


@dataclass(frozen=True)
class FrameData:
    """Wrapper for a numpy array containing the frame image data."""

    data: npt.NDArray[np.uint8]
    """Frame image data."""
