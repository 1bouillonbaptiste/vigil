from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

import numpy as np
import numpy.typing as npt

from vigil.business_logic.models.video_source import VideoSource


class VideoRepository(Protocol):
    """Interface for storing and reading videos."""

    def save(self, source: VideoSource, data: bytes) -> None:
        """Persist raw video bytes under the given source."""
        ...

    def read(self, video_id: UUID) -> Iterable[npt.NDArray[np.uint8]]:
        """Read frames from a stored video."""
        ...

    def frame_count(self, video_id: UUID) -> int:
        """Return the total number of frames in a stored video."""
        ...
