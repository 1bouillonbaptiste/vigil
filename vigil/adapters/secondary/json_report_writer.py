import json
from pathlib import Path
from uuid import UUID

from vigil.business_logic.models.detection import BoundingBox
from vigil.business_logic.models.object_class import ObjectClass
from vigil.business_logic.models.report import Report, TrackSummary


def _bbox_to_dict(bbox: BoundingBox) -> dict:
    return {
        "center_x": bbox.center_x,
        "center_y": bbox.center_y,
        "width": bbox.width,
        "height": bbox.height,
    }


def _summary_to_dict(summary: TrackSummary) -> dict:
    return {
        "track_id": str(summary.track_id),
        "object_class": summary.object_class.value,
        "first_frame_index": summary.first_frame_index,
        "last_frame_index": summary.last_frame_index,
        "first_bbox": _bbox_to_dict(summary.first_bbox),
        "last_bbox": _bbox_to_dict(summary.last_bbox),
        "thumbnail_detection_id": str(summary.thumbnail_detection_id),
    }


def report_to_dict(report: Report) -> dict:
    """Serialise a Report to a JSON-compatible dict."""
    return {
        "video_id": str(report.video_id),
        "track_summaries": [_summary_to_dict(s) for s in report.track_summaries],
    }


def _dict_to_report(data: dict) -> Report:
    """Deserialise a dict (from JSON) back to a Report domain object."""
    return Report(
        video_id=UUID(data["video_id"]),
        track_summaries=[
            TrackSummary(
                track_id=UUID(ts["track_id"]),
                object_class=ObjectClass(ts["object_class"]),
                first_frame_index=ts["first_frame_index"],
                last_frame_index=ts["last_frame_index"],
                first_bbox=BoundingBox(**ts["first_bbox"]),
                last_bbox=BoundingBox(**ts["last_bbox"]),
                thumbnail_detection_id=UUID(ts["thumbnail_detection_id"]),
            )
            for ts in data["track_summaries"]
        ],
    )


class JsonReportWriter:
    """Write analysis reports to disk as JSON files named {video_id}.json."""

    def __init__(self, reports_dir: str = "reports") -> None:
        self._dir = Path(reports_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def write(self, report: Report) -> None:
        """Write the report to disk as {video_id}.json (idempotent)."""
        path = self._dir / f"{report.video_id}.json"
        path.write_text(json.dumps(report_to_dict(report), indent=2))


class JsonReportReader:
    """Read analysis reports previously written by JsonReportWriter."""

    def __init__(self, reports_dir: str = "reports") -> None:
        self._dir = Path(reports_dir)

    def read(self, video_id: UUID) -> Report | None:
        """Return the stored report, or None if it does not exist."""
        path = self._dir / f"{video_id}.json"
        if not path.exists():
            return None
        return _dict_to_report(json.loads(path.read_text()))
