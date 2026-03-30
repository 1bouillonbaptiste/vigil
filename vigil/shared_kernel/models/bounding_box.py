from dataclasses import dataclass


@dataclass(frozen=True)
class BoundingBox:
    """Represent the geometric extent of a detected object in a frame."""

    center_x: int
    """X-axis coordinate of the bbox centroid, in pixels from bottom left."""
    center_y: int
    """Y-axis coordinate of the bbox centroid, in pixels from bottom left."""
    width: int
    """Width of the bounding box, in pixels."""
    height: int
    """Height of the bounding box, in pixels."""
