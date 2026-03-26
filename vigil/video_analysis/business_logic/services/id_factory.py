from uuid import NAMESPACE_URL, UUID, uuid5

from vigil.video_analysis.business_logic.models.detection import Detection
from vigil.video_analysis.business_logic.models.frame import FrameId
from vigil.video_analysis.business_logic.models.track import TrackId
from vigil.video_analysis.business_logic.models.video_source import VideoSource


class IdFactory:
    """Identifiers management service.

    All deterministic ID generation lives here. Deterministic means the same
    inputs always produce the same UUID.
    """

    @staticmethod
    def new_video_id(source: VideoSource) -> UUID:
        """Generate a deterministic id for a video from its source URI."""
        return uuid5(NAMESPACE_URL, source.uri)

    @staticmethod
    def new_frame_id(video_id: UUID, position: int) -> FrameId:
        """Generate an id for `Frame`."""
        return FrameId(uuid5(NAMESPACE_URL, f"{video_id}:{position}"))

    @staticmethod
    def new_track_id(detection: Detection) -> TrackId:
        """Generate a deterministic id for a `Track` from its first detection.

        Keyed on frame and bounding box: two different frames can share the same
        bbox, but a single frame cannot contain two identical bboxes.
        """
        return TrackId(uuid5(NAMESPACE_URL, f"{detection.frame_id}:{detection.prediction.bbox}"))
