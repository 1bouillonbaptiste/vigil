from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from vigil.adapters.primary.fastapi.app_dependencies import get_analysis_status_use_case
from vigil.business_logic.exceptions import VideoNotFoundError

router = APIRouter(tags=["videos"])


class VideoStatusResponse(BaseModel):
    """Response returned when the analysis status of a video is retrieved."""

    video_id: UUID
    analyzed_frames: int
    total_frames: int


@router.get(
    "/videos/{video_id}/status",
    response_model=VideoStatusResponse,
    status_code=200,
    summary="Get the analysis status of a video",
    description=(
        "Return the current analysis progress for the given video. "
        "Poll this endpoint to drive a progress indicator. "
        "Once `analyzed_frames == total_frames`, tracks are available via `GET /videos/{video_id}/tracks`."
    ),
    responses={
        200: {"description": "Status retrieved successfully."},
        404: {"description": "Unknown video_id."},
    },
)
def get_video_status(
    video_id: UUID,
    use_case=Depends(get_analysis_status_use_case),
) -> VideoStatusResponse:
    """Return the analysis progress for the given video."""
    try:
        analysis = use_case.execute(video_id=video_id)
    except VideoNotFoundError as err:
        raise HTTPException(status_code=404, detail="Video not found.") from err

    return VideoStatusResponse(
        video_id=video_id,
        analyzed_frames=analysis.analyzed_frames,
        total_frames=analysis.total_frames,
    )
