from dataclasses import dataclass
from uuid import UUID

from vigil.business_logic.models.detection import BoundingBox
from vigil.business_logic.models.object_class import ObjectClass


@dataclass(frozen=True)
class TrackSummary:
    """Summary of a single tracked object, suitable for inclusion in an analysis report."""

    track_id: UUID
    """Unique identifier of the track."""

    object_class: ObjectClass
    """Detected class of the tracked object."""

    first_frame_index: int
    """Frame index in the source video when the object first appeared."""

    last_frame_index: int
    """Frame index in the source video when the object last appeared."""

    first_bbox: BoundingBox
    """Bounding box at the object's first appearance."""

    last_bbox: BoundingBox
    """Bounding box at the object's last appearance."""

    thumbnail_detection_id: UUID
    """ID of the most visually representative detection (highest visibility score)."""


@dataclass(frozen=True)
class Report:
    """Structured analysis report for a single video."""

    video_id: UUID
    """Identifier of the analysed video."""

    track_summaries: list[TrackSummary]
    """One entry per tracked object. Empty if no valid tracks were found."""
