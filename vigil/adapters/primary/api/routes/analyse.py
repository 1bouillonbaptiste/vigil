from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.iou_tracker import IouTracker
from vigil.adapters.secondary.json_report_writer import report_to_dict
from vigil.business_logic.gateways.video_reader import VideoDurationExceededError
from vigil.business_logic.services.analyse_video import AnalyseVideoService
from vigil.business_logic.use_cases.detect_objects import DetectObjectsUseCase
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase

router = APIRouter()


class AnalyseRequest(BaseModel):
    """Request body for POST /analyse."""

    video_path: str


@router.post("/analyse")
async def analyse(body: AnalyseRequest, request: Request) -> dict:
    """Analyse a recorded video and return a structured report."""
    detection_repo = InMemoryDetectionRepository()
    track_repo = InMemoryTrackRepository()
    tracker = IouTracker()

    detect_uc = DetectObjectsUseCase(
        detection_model=request.app.state.yolo_model,
        detection_repository=detection_repo,
    )
    track_uc = TrackObjectsUseCase(
        detection_repository=detection_repo,
        tracker=tracker,
        track_repository=track_repo,
    )
    service = AnalyseVideoService(
        video_reader=request.app.state.video_reader,
        detect_objects_uc=detect_uc,
        track_objects_uc=track_uc,
        track_repository=track_repo,
        detection_repository=detection_repo,
        report_writer=request.app.state.report_writer,
        frame_interval=5,
    )

    video_id = uuid4()
    try:
        report = service.execute(body.video_path, video_id)
    except FileNotFoundError as err:
        raise HTTPException(status_code=400, detail=f"Video file not found or unreadable: {body.video_path}") from err
    except VideoDurationExceededError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return report_to_dict(report)


@router.get("/reports/{video_id}")
async def get_report(video_id: str, request: Request) -> dict:
    """Retrieve a previously completed analysis report by video ID."""
    from uuid import UUID

    try:
        uid = UUID(video_id)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=f"Invalid video_id format: {video_id}") from err

    report = request.app.state.report_reader.read(uid)
    if report is None:
        raise HTTPException(status_code=404, detail=f"No report found for video_id {video_id}")

    return report_to_dict(report)
