from fastapi import Depends
from starlette.requests import Request

from vigil.monitoring.business_logic.gateways.analysis_job_repository import AnalysisJobRepository
from vigil.monitoring.business_logic.use_cases.get_analysis_status import GetAnalysisStatusUseCase
from vigil.shared_kernel.gateways.domain_event_publisher import DomainEventPublisher
from vigil.video_analysis.adapters.secondary.bytetrack_tracker import make_bytetrack_tracker
from vigil.video_analysis.business_logic.gateways.detection_model import DetectionModel
from vigil.video_analysis.business_logic.gateways.track_repository import TrackRepository
from vigil.video_analysis.business_logic.gateways.tracker import Tracker
from vigil.video_analysis.business_logic.gateways.video_repository import VideoRepository
from vigil.video_analysis.business_logic.use_cases.detect_objects import DetectObjectsUseCase
from vigil.video_analysis.business_logic.use_cases.get_video_tracks import GetVideoTracksUseCase
from vigil.video_analysis.business_logic.use_cases.save_video import SaveVideoUseCase
from vigil.video_analysis.business_logic.use_cases.track_objects import TrackObjectsUseCase


def _get_domain_event_publisher(request: Request) -> DomainEventPublisher:
    return request.app.state.domain_event_publisher


def _get_video_repository(request: Request) -> VideoRepository:
    return request.app.state.video_repository


def _get_detection_model(request: Request) -> DetectionModel:
    return request.app.state.detection_model


def _get_track_repository(request: Request) -> TrackRepository:
    return request.app.state.track_repository


def _get_tracker() -> Tracker:
    """Generate a new tracker per video analysis.

    Trackers may be stateful (e.g. Kalman filters); reusing one across analyses
    produces incorrect results. Creating a fresh instance costs near zero and
    guarantees isolation.
    """
    return make_bytetrack_tracker()


def _get_analysis_job_repository(request: Request) -> AnalysisJobRepository:
    return request.app.state.analysis_job_repository


def get_analysis_status_use_case(
    analysis_job_repository=Depends(_get_analysis_job_repository),
) -> GetAnalysisStatusUseCase:
    """Get the `GetAnalysisStatusUseCase`."""
    return GetAnalysisStatusUseCase(analysis_job_repository=analysis_job_repository)


def get_save_video_use_case(
    video_repository=Depends(_get_video_repository),
    domain_event_publisher=Depends(_get_domain_event_publisher),
) -> SaveVideoUseCase:
    """Get the `SaveVideoUseCase`."""
    return SaveVideoUseCase(video_repository=video_repository, domain_event_publisher=domain_event_publisher)


def get_video_tracks_use_case(
    track_repository=Depends(_get_track_repository),
) -> GetVideoTracksUseCase:
    """Get the `GetVideoTracksUseCase`."""
    return GetVideoTracksUseCase(track_repository=track_repository)


def get_detect_objects_use_case(
    domain_event_publisher=Depends(_get_domain_event_publisher),
    video_repository=Depends(_get_video_repository),
    detection_model=Depends(_get_detection_model),
) -> DetectObjectsUseCase:
    """Get the `DetectObjectsUseCase`."""
    return DetectObjectsUseCase(
        domain_event_publisher=domain_event_publisher,
        video_repository=video_repository,
        detection_model=detection_model,
        batch_size=8,
    )


def get_track_objects_use_case(
    tracker=Depends(_get_tracker),
    track_repository=Depends(_get_track_repository),
) -> TrackObjectsUseCase:
    """Get the `TrackObjectsUseCase`."""
    return TrackObjectsUseCase(tracker=tracker, track_repository=track_repository)
