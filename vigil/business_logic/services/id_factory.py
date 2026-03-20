from uuid import NAMESPACE_URL, UUID, uuid5

from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.frame import FrameId
from vigil.business_logic.models.track import TrackId


class IdFactory:
    """Identifiers management service.

    All deterministic ID generation lives here. Deterministic means the same
    inputs always produce the same UUID.
    """

    @staticmethod
    def new_video_id(uri: str) -> UUID:
        """Generate a deterministic id for a video from its URI."""
        return uuid5(NAMESPACE_URL, uri)

    @staticmethod
    def new_frame_id(video_id: UUID, position: int) -> FrameId:
        """Generate an id for `Frame`."""
        return FrameId(uuid5(NAMESPACE_URL, f"{video_id}:{position}"))

    @staticmethod
    def new_track_id(detection: Detection) -> TrackId:
        """Generate an id for `Track`.

        The id is deterministic for reusability.
        A bbox is a value object given a frame:
        two different frame can have the same bbox, but a single frame cannot hold the same two bboxes.
        """
        return TrackId(uuid5(NAMESPACE_URL, f"{detection.frame_id}:{detection.bbox}"))
