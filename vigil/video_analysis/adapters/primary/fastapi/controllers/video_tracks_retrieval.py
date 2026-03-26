from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vigil.video_analysis.adapters.primary.fastapi.app_dependencies import (
    get_video_tracks_use_case,
)

router = APIRouter(tags=["videos"])


@dataclass
class BoundingBoxResponse:
    """Serialised bounding box for an API response."""

    center_x: int
    center_y: int
    width: int
    height: int


@dataclass
class DetectionResponse:
    """Serialised detection for an API response."""

    frame_position: int
    label: str
    confidence: float
    bbox: BoundingBoxResponse


@dataclass
class TrackResponse:
    """Serialised track for an API response."""

    id: UUID
    closed: bool
    detections: list[DetectionResponse]


class GetVideoTracksResponse(BaseModel):
    """Response returned when tracks are successfully retrieved for a video."""

    status: str
    tracks: list[TrackResponse]


@router.get(
    "/videos/{video_id}/tracks",
    response_model=GetVideoTracksResponse,
    status_code=200,
    summary="Get tracks for a video",
    description="Return all object tracks produced by the analysis pipeline for the given video.",
)
def get_video_tracks(
    video_id: UUID,
    use_case=Depends(get_video_tracks_use_case),
) -> GetVideoTracksResponse:
    """Return all tracks (open and closed) for the given video."""
    tracks = use_case.execute(video_id=video_id)
    return GetVideoTracksResponse(
        status="success",
        tracks=[
            TrackResponse(
                id=track.id,
                closed=track.closed,
                detections=[
                    DetectionResponse(
                        frame_position=detection.frame_position,
                        label=detection.prediction.label,
                        confidence=detection.prediction.confidence,
                        bbox=BoundingBoxResponse(
                            center_x=detection.prediction.bbox.center_x,
                            center_y=detection.prediction.bbox.center_y,
                            width=detection.prediction.bbox.width,
                            height=detection.prediction.bbox.height,
                        ),
                    )
                    for detection in track.detections
                ],
            )
            for track in tracks
        ],
    )
