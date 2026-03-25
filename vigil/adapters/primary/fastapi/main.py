import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Final

from fastapi import FastAPI

from vigil.adapters.primary.fastapi.config import AppConfig
from vigil.adapters.primary.fastapi.controllers import video_analysis, video_status, video_tracks_retrieval
from vigil.adapters.secondary.in_memory_domain_event_publisher import InMemoryDomainEventPublisher
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.adapters.secondary.yolo_detection_model import make_yolo_detection_model
from vigil.business_logic.models.frame_analyzed import FrameAnalyzed
from vigil.business_logic.services.analysis_progress_projection import AnalysisProgressProjection

_CONFIG_PATH: Final[Path] = Path(__file__).parent / "config.yaml"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    config = AppConfig.from_yaml(_CONFIG_PATH)
    video_repository = LocalVideoRepository(storage_dir=Path(tempfile.mkdtemp()))
    publisher: InMemoryDomainEventPublisher[FrameAnalyzed] = InMemoryDomainEventPublisher()
    progress_projection = AnalysisProgressProjection()
    publisher.subscribe(progress_projection)
    detection_model = make_yolo_detection_model(model_name=config.model)
    track_repository = InMemoryTrackRepository()

    app.state.video_repository = video_repository
    app.state.publisher = publisher
    app.state.progress_projection = progress_projection
    app.state.detection_model = detection_model
    app.state.track_repository = track_repository

    yield


app = FastAPI(
    title="Vigil",
    version="1.0.0",
    description=("Video scene understanding API. Submit a video to detect and track objects across frames. "),
    lifespan=lifespan,
)

app.include_router(video_analysis.router)
app.include_router(video_status.router)
app.include_router(video_tracks_retrieval.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
