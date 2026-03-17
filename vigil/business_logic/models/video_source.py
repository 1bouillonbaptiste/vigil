from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5


@dataclass(frozen=True)
class VideoSource:
    """Represent a video identification in a storage system."""

    uri: str
    """The URI of the video source on a given storage system."""

    @property
    def video_id(self) -> UUID:
        """Generate the video source identifier."""
        return uuid5(NAMESPACE_URL, self.uri)
