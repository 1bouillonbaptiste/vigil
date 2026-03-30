from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

import cv2
import numpy as np

from vigil.embedding.business_logic.gateways.frame_reader import FrameReader
from vigil.shared_kernel.models.bounding_box import BoundingBox
from vigil.shared_kernel.models.image import Image
from vigil.video_analysis.business_logic.exceptions import VideoNotFoundError
from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.id_factory import IdFactory


@dataclass
class LocalVideoRepository(VideoRepository, FrameReader):
    """Store video files on the local filesystem and read frames via OpenCV."""

    storage_dir: Path
    _paths: dict[UUID, Path] = field(default_factory=dict, init=False)
    _frame_counts: dict[UUID, int] = field(default_factory=dict, init=False)

    def save(self, source: VideoSource, data: bytes) -> None:
        """Write raw video bytes to disk and cache the exact frame count."""
        path = self.storage_dir / source.uri
        path.write_bytes(data)
        video_id = IdFactory.new_video_id(source)
        self._paths[video_id] = path
        self._frame_counts[video_id] = self._count_frames(path)

    @staticmethod
    def _count_frames(path: Path) -> int:
        """Count frames by grabbing without decoding."""
        cap = cv2.VideoCapture(str(path))
        count = 0
        while cap.grab():
            count += 1
        cap.release()
        return count

    def read(self, video_id: UUID) -> Iterator[Image]:
        """Yield frames from the stored video in position order."""
        if video_id not in self._paths:
            raise VideoNotFoundError(video_id)
        cap = cv2.VideoCapture(str(self._paths[video_id]))
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                yield Image(frame.astype(np.uint8))
        finally:
            cap.release()

    def frame_count(self, video_id: UUID) -> int:
        """Return the total number of frames in the stored video."""
        if video_id not in self._paths:
            raise VideoNotFoundError(video_id)
        return self._frame_counts[video_id]

    def read_crop(self, video_id: UUID, frame_position: int, bbox: BoundingBox) -> Image:
        """Seek to `frame_position` and return the region clipped to `bbox`."""
        if video_id not in self._paths:
            raise VideoNotFoundError(video_id)
        cap = cv2.VideoCapture(str(self._paths[video_id]))
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
            ret, frame = cap.read()
            if not ret:
                raise ValueError(f"Could not read frame {frame_position} for video {video_id}")
            frame_height = frame.shape[0]
            x1 = bbox.center_x - bbox.width // 2
            y1 = frame_height - bbox.center_y - bbox.height // 2
            x2 = x1 + bbox.width
            y2 = y1 + bbox.height
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame_height, y2)
            return Image(frame[y1:y2, x1:x2].astype(np.uint8))
        finally:
            cap.release()
