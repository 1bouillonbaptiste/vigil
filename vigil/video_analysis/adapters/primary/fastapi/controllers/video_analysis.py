from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from pydantic import BaseModel, Field

from vigil.video_analysis.adapters.primary.fastapi.app_dependencies import (
    _get_track_repository,
    _get_tracker,
    get_detect_objects_use_case,
    get_save_video_use_case,
)
from vigil.video_analysis.business_logic.gateways.track_repository import TrackRepository
from vigil.video_analysis.business_logic.gateways.tracker import Tracker
from vigil.video_analysis.business_logic.models.track import Track
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.id_factory import IdFactory
from vigil.video_analysis.business_logic.use_cases.detect_objects import DetectObjectsUseCase

router = APIRouter(tags=["videos"])


class AnalyseVideoResponse(BaseModel):
    """Response returned when a video is successfully submitted for analysis."""

    video_id: UUID = Field(
        description=("Unique identifier for the submitted video. Use this ID to poll for analysis results."),
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )


def _run_analysis(
    video_id: UUID, detect_objects: DetectObjectsUseCase, tracker: Tracker, track_repository: TrackRepository
) -> None:
    detections = detect_objects.execute(video_id)
    for sequence in tracker.track(detections):
        track_repository.save(
            Track(
                id=IdFactory.new_track_id(sequence[0]),
                video_id=video_id,
                detections=tuple(sequence),
            )
        )


@router.post(
    "/analyze-video",
    response_model=AnalyseVideoResponse,
    status_code=202,
    summary="Submit a video for analysis",
    description=(
        "Upload a video file to start object detection and tracking. "
        "The video is saved and analyzed asynchronously — the response is "
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
    detect_objects_use_case=Depends(get_detect_objects_use_case),
    tracker=Depends(_get_tracker),
    track_repository=Depends(_get_track_repository),
) -> AnalyseVideoResponse:
    """Accept a video file, persist it, and start the analysis pipeline.

    The analysis (detection + tracking) runs as a background task. The caller
    receives the `video_id` immediately and can use it to poll for results.
    """
    source = VideoSource(uri=file.filename or "video")
    data = await file.read()
    video_id = save_video_use_case.execute(source=source, data=data)
    background_tasks.add_task(_run_analysis, video_id, detect_objects_use_case, tracker, track_repository)
    return AnalyseVideoResponse(video_id=video_id)
