from uuid import UUID

from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import Detection


class IouTracker(Tracker):
    """Implement a tracker with iou comparison across frames.

    The tracker needs to order detections chronologically to decide whether two consecutive detections belong to the
    same instance.
    Frame ordering is not stored on detections (it lives on VideoFrame.position) so a FrameRepository is injected to
    resolve the position of each frame referenced by the input detections.
    This keeps Detection free of positional metadata while still allowing the algorithm to sort and group detections
    by frame order.
    """

    def __init__(self, frame_repository: FrameRepository, min_iou: float = 0):
        self._frame_repository = frame_repository
        self.min_iou = min_iou

    def track(self, detections: list[Detection]) -> list[list[Detection]]:
        """Continue a track with the highest iou detection within the next frame."""
        if len(detections) < 2:
            return [detections]

        frame_positions = self._get_frame_positions(detections)

        tracks: list[list[Detection]] = []
        remaining_detections: list[Detection] = sorted(detections, key=lambda d: frame_positions[d.frame_id])
        current_track: list[Detection] = [remaining_detections.pop(0)]
        while remaining_detections:
            current_position = frame_positions[current_track[-1].frame_id]
            next_frame_detections = self._find_detections_at_position(
                remaining_detections, frame_positions, current_position + 1
            )
            if not next_frame_detections:
                tracks.append(current_track)
                current_track = [remaining_detections.pop(0)]
                continue
            best_match = max(next_frame_detections, key=lambda other: self._distance(current_track[-1], other))
            if self._distance(current_track[-1], best_match) <= self.min_iou:
                tracks.append(current_track)
                current_track = [remaining_detections.pop(0)]
                continue
            current_track.append(best_match)
            remaining_detections.remove(best_match)

        tracks.append(current_track)
        return tracks

    def _get_frame_positions(self, detections: list[Detection]) -> dict[UUID, int]:
        """Load the frames referenced by detections and return a frame_id -> position mapping."""
        frame_ids = {d.frame_id for d in detections}
        return {frame_id: self._frame_repository.get_by_id(frame_id).position for frame_id in frame_ids}

    @staticmethod
    def _find_detections_at_position(
        detections: list[Detection], frame_positions: dict[UUID, int], position: int
    ) -> list[Detection]:
        """Find all detections within a frame at the given position."""
        return [detection for detection in detections if frame_positions[detection.frame_id] == position]

    @staticmethod
    def _distance(detection1: Detection, detection2: Detection) -> float:
        """Calculate the iou between two detections."""
        xA = max(detection1.bbox.bottom_left[0], detection2.bbox.bottom_left[0])
        yA = max(detection1.bbox.bottom_left[1], detection2.bbox.bottom_left[1])
        xB = min(detection1.bbox.top_right[0], detection2.bbox.top_right[0])
        yB = min(detection1.bbox.top_right[1], detection2.bbox.top_right[1])

        intersection_area = max(0, xB - xA) * max(0, yB - yA)
        iou = intersection_area / float(detection1.bbox.area + detection2.bbox.area - intersection_area)

        return iou
