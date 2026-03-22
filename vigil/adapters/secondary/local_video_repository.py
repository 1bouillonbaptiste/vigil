from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

import cv2
import numpy as np
import numpy.typing as npt

from vigil.business_logic.exceptions import VideoNotFoundError
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.id_factory import IdFactory


@dataclass
class LocalVideoRepository:
    """Store video files on the local filesystem and read frames via OpenCV."""

    storage_dir: Path
    _paths: dict[UUID, Path] = field(default_factory=dict, init=False)

    def save(self, source: VideoSource, data: bytes) -> None:
        """Write raw video bytes to disk."""
        path = self.storage_dir / source.uri
        path.write_bytes(data)
        self._paths[IdFactory.new_video_id(source)] = path

    def read(self, video_id: UUID) -> Iterator[npt.NDArray[np.uint8]]:
        """Yield frames from the stored video in position order."""
        if video_id not in self._paths:
            raise VideoNotFoundError(video_id)
        cap = cv2.VideoCapture(str(self._paths[video_id]))
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                yield frame.astype(np.uint8)
        finally:
            cap.release()

    def frame_count(self, video_id: UUID) -> int:
        """Return the total number of frames in the stored video."""
        if video_id not in self._paths:
            raise VideoNotFoundError(video_id)
        cap = cv2.VideoCapture(str(self._paths[video_id]))
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return count
