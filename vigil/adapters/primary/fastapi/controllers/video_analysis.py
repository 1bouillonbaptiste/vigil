from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel

from vigil.adapters.primary.fastapi.app_dependencies import get_save_video_use_case
from vigil.business_logic.models.video_source import VideoSource

router = APIRouter()


class AnalyseVideoResponse(BaseModel):
    """Response for video analysis post request."""

    video_id: UUID


@router.post("/analyze-video", response_model=AnalyseVideoResponse, status_code=202)
async def analyze_video(
    file: UploadFile,
    save_video_use_case=Depends(get_save_video_use_case),
) -> AnalyseVideoResponse:
    """Analyze video post request."""
    source = VideoSource(uri=file.filename or "video")
    data = await file.read()
    video_id = save_video_use_case.execute(source=source, data=data)
    return AnalyseVideoResponse(video_id=video_id)
