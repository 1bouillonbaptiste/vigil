import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Final

from fastapi import FastAPI

from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.video_analysis.adapters.primary.events_subscriber.frame_detected_subscriber import FrameDetectedSubscriber
from vigil.video_analysis.adapters.primary.fastapi.config import AppConfig
from vigil.video_analysis.adapters.primary.fastapi.controllers import (
    video_analysis,
    video_status,
    video_tracks_retrieval,
)
from vigil.video_analysis.adapters.secondary.in_memory_analysis_progression_projection import (
    InMemoryAnalysisProgressionProjection,
)
from vigil.video_analysis.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.video_analysis.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.video_analysis.adapters.secondary.yolo_detection_model import make_yolo_detection_model

_CONFIG_PATH: Final[Path] = Path(__file__).parent / "config.yaml"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # Shared kernel
    domain_event_publisher = InMemoryEventPublisher()
    app.state.domain_event_publisher = domain_event_publisher

    config = AppConfig.from_yaml(_CONFIG_PATH)
    video_repository = LocalVideoRepository(storage_dir=Path(tempfile.mkdtemp()))
    detection_model = make_yolo_detection_model(model_name=config.model)
    track_repository = InMemoryTrackRepository()
    analysis_progression = InMemoryAnalysisProgressionProjection()

    FrameDetectedSubscriber(publisher=domain_event_publisher, analysis_progression=analysis_progression).subscribe()

    app.state.video_repository = video_repository
    app.state.detection_model = detection_model
    app.state.track_repository = track_repository
    app.state.analysis_progression = analysis_progression

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
