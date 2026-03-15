from dataclasses import dataclass


@dataclass(frozen=True)
class RawFrame:
    """A single video frame represented as JPEG-encoded bytes.

    Used as the exchange type between the VideoReader port and the
    DetectionModel port. Keeps numpy arrays out of the application layer.
    """

    index: int
    """Actual frame index in the source video (e.g. 0, 5, 10 … with 1-in-5 sampling)."""

    data: bytes
    """JPEG-encoded image data."""
