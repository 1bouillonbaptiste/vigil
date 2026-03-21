from fastapi import Depends
from starlette.requests import Request

from vigil.business_logic.gateways.video_repository import VideoRepository
from vigil.business_logic.use_cases.save_video import SaveVideoUseCase


def get_video_repository(request: Request) -> VideoRepository:
    """Get the production video repository."""
    return request.app.state.video_repository


def get_save_video_use_case(
    video_repository=Depends(get_video_repository),
) -> SaveVideoUseCase:
    """Get the `SaveVideoUseCase`."""
    return SaveVideoUseCase(video_repository=video_repository)
