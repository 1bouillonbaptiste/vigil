from uuid import NAMESPACE_URL, UUID, uuid5

from vigil.business_logic.models.detection import BoundingBox


class IdFactory:
    """Identifiers management service.

    Manage ids where deterministic ids are mandatory: ...
    """

    @staticmethod
    def new_detection_id(frame_id: UUID, bbox: BoundingBox) -> UUID:
        """Generate an id for `Detection`."""
        return uuid5(NAMESPACE_URL, f"{frame_id}:{bbox}")

    @staticmethod
    def new_frame_id(video_id: UUID, position: int) -> UUID:
        """Generate an id for `VideoFrame`."""
        return uuid5(NAMESPACE_URL, f"{video_id}:{position}")
