from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import numpy.typing as npt
from ultralytics.trackers.byte_tracker import BYTETracker

from vigil.video_analysis.business_logic.models.detection import ClassLabel, Detection

_CLASS_TO_INT: dict[ClassLabel, int] = {ClassLabel.PERSON: 0, ClassLabel.VEHICLE: 1}

# Output column indices from BYTETracker.update()
# Each row: [x1, y1, x2, y2, track_id, score, cls, det_idx]
_COL_TRACK_ID = 4
_COL_DET_IDX = 7


@dataclass
class _ByteTrackResults:
    """Detection array wrapper for BYTETracker.update()."""

    conf: npt.NDArray[np.float32]
    xywh: npt.NDArray[np.float32]
    cls: npt.NDArray[np.float32]

    def __len__(self) -> int:
        return len(self.conf)

    def __getitem__(self, mask: npt.NDArray[np.bool_]) -> "_ByteTrackResults":
        return _ByteTrackResults(conf=self.conf[mask], xywh=self.xywh[mask], cls=self.cls[mask])


def _to_bytetrack_results(detections: list[Detection]) -> _ByteTrackResults:
    return _ByteTrackResults(
        conf=np.array([d.prediction.confidence for d in detections], dtype=np.float32),
        xywh=np.array(
            [
                [
                    d.prediction.bbox.center_x,
                    d.prediction.bbox.center_y,
                    d.prediction.bbox.width,
                    d.prediction.bbox.height,
                ]
                for d in detections
            ],
            dtype=np.float32,
        ),
        cls=np.array([_CLASS_TO_INT[d.prediction.label] for d in detections], dtype=np.float32),
    )


class ByteTrackTracker:
    """Tracker adapter backed by ByteTrack.

    Walks the detection sequence frame by frame, feeds each frame to
    BYTETracker, and groups detections that ByteTrack assigns to the same
    integer track ID. The grouping is returned as a list of detection
    sequences — one per tracked object.

    This adapter is stateful (Kalman filters). Use a fresh instance per
    video analysis via ``make_bytetrack_tracker()``.
    """

    def __init__(self, bytetracker: BYTETracker) -> None:
        self._bytetracker = bytetracker

    def track(self, detections: list[Detection]) -> list[list[Detection]]:
        """Group detections belonging to the same object across frames."""
        if not detections:
            return []

        by_frame: dict[int, list[Detection]] = {}
        for d in detections:
            by_frame.setdefault(d.frame_position, []).append(d)

        groups: dict[int, list[Detection]] = {}

        for frame_pos in sorted(by_frame):
            frame_detections = by_frame[frame_pos]
            raw = self._bytetracker.update(_to_bytetrack_results(frame_detections))

            for row in raw:
                bytetrack_id = int(row[_COL_TRACK_ID])
                det_idx = int(row[_COL_DET_IDX])
                groups.setdefault(bytetrack_id, []).append(frame_detections[det_idx])

        return list(groups.values())


def make_bytetrack_tracker(frame_rate: int = 30) -> ByteTrackTracker:
    """Create a ByteTrackTracker with sensible defaults."""
    args = SimpleNamespace(
        track_high_thresh=0.5,
        track_low_thresh=0.1,
        new_track_thresh=0.6,
        track_buffer=30,
        match_thresh=0.8,
        fuse_score=False,
    )
    return ByteTrackTracker(BYTETracker(args, frame_rate=frame_rate))
