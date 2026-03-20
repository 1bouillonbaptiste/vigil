from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

import numpy as np
import numpy.typing as npt


class VideoReader(Protocol):
    """Interface for reading videos from a source."""

    def read(self, video_id: UUID) -> Iterable[npt.NDArray[np.uint8]]:
        """Read frames from a video."""
        ...
