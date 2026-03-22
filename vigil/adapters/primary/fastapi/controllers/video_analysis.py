from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from pydantic import BaseModel, Field

from vigil.adapters.primary.fastapi.app_dependencies import get_save_video_use_case, get_video_analysis_workflow
from vigil.business_logic.models.video_source import VideoSource

router = APIRouter(tags=["videos"])


class AnalyseVideoResponse(BaseModel):
    """Response returned when a video is successfully submitted for analysis."""

    video_id: UUID = Field(
        description=("Unique identifier for the submitted video. Use this ID to poll for analysis results."),
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )


@router.post(
    "/analyze-video",
    response_model=AnalyseVideoResponse,
    status_code=202,
    summary="Submit a video for analysis",
    description=(
        "Upload a video file to start object detection and tracking. "
        "The video is saved and analysed asynchronously — the response is "
        "returned immediately with a `video_id` that can be used to retrieve "
        "results once processing is complete."
    ),
    responses={
        202: {"description": "Video accepted, analysis started in the background."},
        422: {"description": "Invalid or missing video file."},
    },
)
async def analyze_video(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    save_video_use_case=Depends(get_save_video_use_case),
    video_analysis_workflow=Depends(get_video_analysis_workflow),
) -> AnalyseVideoResponse:
    """Accept a video file, persist it, and start the analysis pipeline.

    The analysis (detection + tracking) runs as a background task. The caller
    receives the `video_id` immediately and can use it to poll for results.
    """
    source = VideoSource(uri=file.filename or "video")
    data = await file.read()
    video_id = save_video_use_case.execute(source=source, data=data)
    background_tasks.add_task(video_analysis_workflow.execute, video_id)
    return AnalyseVideoResponse(video_id=video_id)
