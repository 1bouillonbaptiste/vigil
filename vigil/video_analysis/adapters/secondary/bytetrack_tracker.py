from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import numpy.typing as npt
from ultralytics.trackers.byte_tracker import BYTETracker

from vigil.video_analysis.business_logic.models.detection import ClassLabel, Detection
from vigil.video_analysis.business_logic.models.track import Track

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

    ByteTrack manages its own internal Kalman-filter state and assigns integer
    track IDs.  This adapter maps those integer IDs back to domain Tracks by
    storing the spawning Detection for each ByteTrack ID, then searching the
    tracks list for the Track whose first Detection matches.

    Assumption: the caller creates a new domain Track for every Detection that
    this adapter returns as an orphan (i.e. absent from the matched pairs).
    The mapping from ByteTrack integer IDs to domain Tracks relies on finding,
    in the next call's ``tracks`` list, the Track whose first detection equals
    the spawning detection recorded here.  If the caller does not create that
    Track, the ByteTrack ID will never resolve and the object will be treated
    as a new track on every subsequent frame.
    """

    def __init__(self, bytetracker: BYTETracker) -> None:
        self._bytetracker = bytetracker
        self._track_origin: dict[int, Detection] = {}  # bytetrack_id → spawning detection

    def update(self, tracks: list[Track], detections: list[Detection]) -> list[tuple[Track, Detection]]:
        """Assign new detections to existing open tracks via ByteTrack."""
        if not detections:
            return []

        results = _to_bytetrack_results(detections)
        raw = self._bytetracker.update(results)  # (M, 8): [x1,y1,x2,y2,track_id,score,cls,det_idx]

        if len(raw) == 0:
            return []

        tracks_by_first_detection: dict[Detection, Track] = {t.detections[0]: t for t in tracks}
        matches: list[tuple[Track, Detection]] = []

        for row in raw:
            bytetrack_id = int(row[_COL_TRACK_ID])
            det_idx = int(row[_COL_DET_IDX])
            detection = detections[det_idx]

            if bytetrack_id not in self._track_origin:
                # New internal track — record the spawning detection so we can
                # locate the domain Track on the next frame.
                self._track_origin[bytetrack_id] = detection
                continue

            domain_track = tracks_by_first_detection.get(self._track_origin[bytetrack_id])
            if domain_track is None:
                # Domain track was closed or not yet created; skip.
                continue

            matches.append((domain_track, detection))

        return matches


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
