from dataclasses import dataclass


@dataclass(frozen=True)
class VideoSource:
    """Represent a video identification in a storage system."""

    uri: str
    """The URI of the video source on a given storage system."""
