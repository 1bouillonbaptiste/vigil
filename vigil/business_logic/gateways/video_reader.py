from collections.abc import Iterable
from typing import Protocol

import numpy as np
import numpy.typing as npt

from vigil.business_logic.models.video_source import VideoSource


class VideoReader(Protocol):
    """Interface for reading videos from a source."""

    def read(self, source: VideoSource) -> Iterable[npt.NDArray[np.uint8]]:
        """Read frames from a video."""
        ...
