from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from pydantic import BaseModel

from vigil.adapters.primary.fastapi.app_dependencies import get_save_video_use_case, get_video_analysis_workflow
from vigil.business_logic.models.video_source import VideoSource

router = APIRouter()


class AnalyseVideoResponse(BaseModel):
    """Response for video analysis post request."""

    video_id: UUID


@router.post("/analyze-video", response_model=AnalyseVideoResponse, status_code=202)
async def analyze_video(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    save_video_use_case=Depends(get_save_video_use_case),
    video_analysis_workflow=Depends(get_video_analysis_workflow),
) -> AnalyseVideoResponse:
    """Analyze video post request."""
    source = VideoSource(uri=file.filename or "video")
    data = await file.read()
    video_id = save_video_use_case.execute(source=source, data=data)
    background_tasks.add_task(video_analysis_workflow.execute, video_id)
    return AnalyseVideoResponse(video_id=video_id)
