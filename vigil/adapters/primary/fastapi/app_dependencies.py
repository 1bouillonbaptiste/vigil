from fastapi import Depends
from starlette.requests import Request

from vigil.adapters.secondary.bytetrack_tracker import make_bytetrack_tracker
from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.gateways.frame_repository import FrameRepository
from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.gateways.video_repository import VideoRepository
from vigil.business_logic.services.detection_service import DetectionService
from vigil.business_logic.use_cases.get_analysis_status import GetAnalysisStatusUseCase
from vigil.business_logic.use_cases.get_video_tracks import GetVideoTracksUseCase
from vigil.business_logic.use_cases.save_video import SaveVideoUseCase
from vigil.business_logic.use_cases.video_analysis_workflow import VideoAnalysisWorkflow


def _get_video_repository(request: Request) -> VideoRepository:
    return request.app.state.video_repository


def _get_frame_repository(request: Request) -> FrameRepository:
    return request.app.state.frame_repository


def _get_detection_model(request: Request) -> DetectionModel:
    return request.app.state.detection_model


def _get_track_repository(request: Request) -> TrackRepository:
    return request.app.state.track_repository


def _get_tracker() -> Tracker:
    return make_bytetrack_tracker()


def _build_detection_service(detection_model=Depends(_get_detection_model)) -> DetectionService:
    return DetectionService(model=detection_model)


def get_analysis_status_use_case(
    frame_repository=Depends(_get_frame_repository),
    video_repository=Depends(_get_video_repository),
) -> GetAnalysisStatusUseCase:
    """Get the `GetAnalysisStatusUseCase`."""
    return GetAnalysisStatusUseCase(frame_repository=frame_repository, video_repository=video_repository)


def get_save_video_use_case(
    video_repository=Depends(_get_video_repository),
) -> SaveVideoUseCase:
    """Get the `SaveVideoUseCase`."""
    return SaveVideoUseCase(video_repository=video_repository)


def get_video_tracks_use_case(
    track_repository=Depends(_get_track_repository),
) -> GetVideoTracksUseCase:
    """Get the `GetVideoTracksUseCase`."""
    return GetVideoTracksUseCase(track_repository=track_repository)


def get_video_analysis_workflow(
    video_repository=Depends(_get_video_repository),
    frame_repository=Depends(_get_frame_repository),
    detection_service=Depends(_build_detection_service),
    tracker=Depends(_get_tracker),
    track_repository=Depends(_get_track_repository),
) -> VideoAnalysisWorkflow:
    """Get the `VideoAnalysisWorkflow`."""
    return VideoAnalysisWorkflow(
        video_repository=video_repository,
        frame_repository=frame_repository,
        detection_service=detection_service,
        tracker=tracker,
        track_repository=track_repository,
        batch_size=8,
    )
