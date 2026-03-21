import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from vigil.adapters.primary.fastapi.controllers import video_analysis
from vigil.adapters.secondary.fake_detection_model import FakeDetectionModel
from vigil.adapters.secondary.fake_tracker import FakeTracker
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.local_video_repository import LocalVideoRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    video_repository = LocalVideoRepository(storage_dir=Path(tempfile.mkdtemp()))
    frame_repository = InMemoryFrameRepository()
    detection_model = FakeDetectionModel()
    track_repository = InMemoryTrackRepository()
    tracker = FakeTracker()

    app.state.video_repository = video_repository
    app.state.frame_repository = frame_repository
    app.state.detection_model = detection_model
    app.state.track_repository = track_repository
    app.state.tracker = tracker

    yield


app = FastAPI(
    title="Vigil",
    version="1.0.0",
    description=(
        "Video scene understanding API. "
        "Submit a video to detect and track objects across frames. "
    ),
    lifespan=lifespan,
)

app.include_router(video_analysis.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
