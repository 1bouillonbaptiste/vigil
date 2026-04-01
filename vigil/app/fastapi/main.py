import logging
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Final

from fastapi import FastAPI

from vigil.app.fastapi.config import AppConfig
from vigil.embedding.adapters.primary.events_subscriber.track_identified_subscriber import TrackIdentifiedSubscriber
from vigil.embedding.adapters.primary.fastapi.controllers import query_by_description
from vigil.embedding.adapters.secondary.clip_embedding_model import ClipEmbeddingModel
from vigil.embedding.adapters.secondary.in_memory_embedded_track_repository import InMemoryEmbeddedTrackRepository
from vigil.embedding.business_logic.services.embedding_matcher import EmbeddingMatcher
from vigil.embedding.business_logic.use_cases.index_track import IndexTrackUseCase
from vigil.monitoring.adapters.primary.events_subscriber.frame_detected_subscriber import (
    FrameDetectedSubscriber as MonitoringFrameDetectedSubscriber,
)
from vigil.monitoring.adapters.primary.events_subscriber.tracking_finished_subscriber import (
    TrackingFinishedSubscriber,
)
from vigil.monitoring.adapters.primary.events_subscriber.video_created_subscriber import VideoCreatedSubscriber
from vigil.monitoring.adapters.secondary.in_memory_analysis_job_repository import InMemoryAnalysisJobRepository
from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.video_analysis.adapters.primary.fastapi.controllers import (
    video_analysis,
    video_status,
    video_tracks_retrieval,
)
from vigil.video_analysis.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.video_analysis.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.video_analysis.adapters.secondary.yolo_detection_model import make_yolo_detection_model

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")

_CONFIG_PATH: Final[Path] = Path(__file__).parent / "config.yaml"
"""Configuration for runtime parameters."""

_NEUTRAL_DESCRIPTION: Final[str] = "a random unrelated scene"
"""Baseline description used to calibrate EmbeddingMatcher probabilities.

CLIP cosine similarities are not calibrated as absolute values, so we score each
image embedding against this neutral description as a reference point.  A track
embedding that scores higher than this baseline is considered a match.
"""


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
    analysis_job_repository = InMemoryAnalysisJobRepository()

    embedded_track_repository = InMemoryEmbeddedTrackRepository()
    embedding_model = ClipEmbeddingModel()
    embedding_matcher = EmbeddingMatcher(neutral_embedding=embedding_model.embed(_NEUTRAL_DESCRIPTION))

    VideoCreatedSubscriber(publisher=domain_event_publisher, repository=analysis_job_repository).subscribe()
    MonitoringFrameDetectedSubscriber(publisher=domain_event_publisher, repository=analysis_job_repository).subscribe()
    TrackingFinishedSubscriber(publisher=domain_event_publisher, repository=analysis_job_repository).subscribe()
    TrackIdentifiedSubscriber(
        publisher=domain_event_publisher,
        use_case=IndexTrackUseCase(
            track_repository=embedded_track_repository,
            frame_reader=video_repository,
            model=embedding_model,
        ),
    ).subscribe()

    app.state.video_repository = video_repository
    app.state.detection_model = detection_model
    app.state.track_repository = track_repository
    app.state.analysis_job_repository = analysis_job_repository
    app.state.embedded_track_repository = embedded_track_repository
    app.state.embedding_model = embedding_model
    app.state.embedding_matcher = embedding_matcher

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
app.include_router(query_by_description.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
