from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BoundingBox:
    """Bounding box coordinates in pixel space."""

    center_x: int
    center_y: int
    width: int
    height: int


@dataclass(frozen=True)
class DetectionData:
    """A single object detection within one video frame."""

    frame_position: int
    label: str
    confidence: float
    bbox: BoundingBox


@dataclass(frozen=True)
class TrackData:
    """An object track composed of per-frame detections."""

    id: str
    detections: tuple[DetectionData, ...]


@dataclass(frozen=True)
class VideoStatus:
    """Current analysis progress for a video."""

    video_id: str
    analyzed_frames: int
    total_frames: int

    @property
    def is_complete(self) -> bool:
        """Return True when all frames have been processed."""
        return self.total_frames > 0 and self.analyzed_frames >= self.total_frames


@dataclass
class VideoEntry:
    """Local state for a video that has been uploaded to the backend."""

    video_id: str
    name: str
    file_path: Path
    status: VideoStatus | None = field(default=None)
