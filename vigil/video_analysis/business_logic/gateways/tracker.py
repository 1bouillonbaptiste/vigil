from typing import Protocol

from vigil.video_analysis.business_logic.models.detection import Detection


class Tracker(Protocol):
    """Interface for object trackers.

    Groups detections belonging to the same object across frames.

    Implementations MAY be stateful (e.g. Kalman filters). If so, a fresh
    instance must be used per video analysis — reusing an instance across videos
    produces incorrect results.
    """

    def track(self, detections: list[Detection]) -> list[list[Detection]]:
        """Group detections belonging to the same object.

        ``detections`` must be ordered by ``frame_position``.

        Returns one list per tracked object; each inner list contains the
        detections for that object ordered by ``frame_position``.
        """
        ...
