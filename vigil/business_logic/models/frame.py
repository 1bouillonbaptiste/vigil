from dataclasses import dataclass, field
from typing import NewType
from uuid import UUID

import numpy as np
import numpy.typing as npt

FrameId = NewType("FrameId", UUID)
"""Frame unique identifier."""


@dataclass(frozen=True)
class Frame:
    """Represent a single frame from a video, including its pixel data."""

    id: FrameId
    """Frame unique identifier."""

    position: int
    """Ordering position of the frame in the video."""

    video_id: UUID
    """Video identifier the frame originally comes from."""

    data: npt.NDArray[np.uint8] = field(hash=False, compare=False)
    """Frame image data."""
