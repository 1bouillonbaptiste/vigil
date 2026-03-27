from typing import Any

from vigil.app.streamlit.components.models import (
    BoundingBox,
    DetectionData,
    TrackData,
    VideoStatus,
)


def video_status_from_payload(payload: dict[str, Any]) -> VideoStatus:
    """Map a raw /videos/{id}/status response dict to a VideoStatus."""
    return VideoStatus(
        video_id=payload["video_id"],
        analyzed_frames=payload["analyzed_frames"],
        total_frames=payload["total_frames"],
    )


def tracks_from_payload(payload: dict[str, Any]) -> list[TrackData]:
    """Map a raw /videos/{id}/tracks response dict to a list of TrackData."""
    return [
        TrackData(
            id=track["id"],
            detections=tuple(
                DetectionData(
                    frame_position=det["frame_position"],
                    label=det["label"],
                    confidence=det["confidence"],
                    bbox=BoundingBox(
                        center_x=det["bbox"]["center_x"],
                        center_y=det["bbox"]["center_y"],
                        width=det["bbox"]["width"],
                        height=det["bbox"]["height"],
                    ),
                )
                for det in track["detections"]
            ),
        )
        for track in payload["tracks"]
    ]
