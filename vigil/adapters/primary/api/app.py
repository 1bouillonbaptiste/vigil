from contextlib import asynccontextmanager

from fastapi import FastAPI

from vigil.adapters.primary.api.routes.analyse import router
from vigil.adapters.secondary.cv2_video_reader import Cv2VideoReader
from vigil.adapters.secondary.json_report_writer import JsonReportReader, JsonReportWriter
from vigil.adapters.secondary.yolo_detection_model import YoloDetectionModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise expensive resources once at startup."""
    app.state.yolo_model = YoloDetectionModel()
    app.state.video_reader = Cv2VideoReader()
    app.state.report_writer = JsonReportWriter()
    app.state.report_reader = JsonReportReader()
    yield


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    app = FastAPI(
        title="Vigil",
        description="Post-hoc structured analysis of recorded video.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
