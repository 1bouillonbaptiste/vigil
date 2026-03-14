from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import Detection


class IouTracker(Tracker):
    """Implement a tracker with iou comparison across frames."""

    def __init__(self, min_iou: float = 0):
        self.min_iou = min_iou

    def track(self, detections: list[Detection]) -> list[list[Detection]]:
        """Continue a track with the highest iou detection within the next frame."""
        if len(detections) < 2:
            return [detections]

        tracks: list[list[Detection]] = []
        remaining_detections: list[Detection] = sorted(detections, key=lambda d: d.frame_index)
        current_track: list[Detection] = [remaining_detections.pop(0)]
        while remaining_detections:
            next_frame_detections = self._find_detections_on_frame(
                remaining_detections, current_track[-1].frame_index + 1
            )
            if not next_frame_detections:
                tracks.append(current_track)
                current_track = [remaining_detections.pop(0)]
                continue
            best_match = max(next_frame_detections, key=lambda other: self._distance(current_track[-1], other))
            if self._distance(current_track[-1], best_match) <= 0:
                tracks.append(current_track)
                current_track = [remaining_detections.pop(0)]
                continue
            current_track.append(best_match)
            remaining_detections.remove(best_match)

        tracks.append(current_track)
        return tracks

    @staticmethod
    def _find_detections_on_frame(detections: list[Detection], frame_idx: int) -> list[Detection]:
        """Find all detections within a frame."""
        return [detection for detection in detections if detection.frame_index == frame_idx]

    @staticmethod
    def _distance(detection1: Detection, detection2: Detection) -> float:
        """Calculate the iou between two detections."""
        # determine the (x, y)-coordinates of the intersection rectangle
        xA = max(detection1.bbox.bottom_left[0], detection2.bbox.bottom_left[0])
        yA = max(detection1.bbox.bottom_left[1], detection2.bbox.bottom_left[1])
        xB = min(detection1.bbox.top_right[0], detection2.bbox.top_right[0])
        yB = min(detection1.bbox.top_right[1], detection2.bbox.top_right[1])

        intersection_area = max(0, xB - xA) * max(0, yB - yA)
        iou = intersection_area / float(detection1.bbox.area + detection2.bbox.area - intersection_area)

        return iou
