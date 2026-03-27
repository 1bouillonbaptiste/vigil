from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from vigil.app.fastapi.main import app
from vigil.video_analysis.adapters.primary.fastapi.app_dependencies import _get_detection_model
from vigil.video_analysis.adapters.secondary.yolo_detection_model import make_yolo_detection_model


@dataclass
class ThisContext:
    """Context for the video analysis journey test."""

    client: TestClient


@pytest.fixture(scope="module")
def this_context() -> Generator[ThisContext, None, None]:
    detection_model = make_yolo_detection_model(model_name="yolov8n")
    app.dependency_overrides[_get_detection_model] = lambda: detection_model
    with TestClient(app) as client:
        yield ThisContext(client=client)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def realistic_video_filepath() -> Path:
    """Return the path to the realistic 10-frame people video fixture."""
    return Path(__file__).parent.parent.parent / "data" / "people_10frames.mp4"


@pytest.fixture(scope="module")
def video_id(this_context: ThisContext, realistic_video_filepath: Path) -> str:
    """Upload a video, run analysis, and return the video_id."""
    with open(realistic_video_filepath, "rb") as f:
        response = this_context.client.post(
            "/analyze-video",
            files={"file": (realistic_video_filepath.name, f, "video/mp4")},
        )
    assert response.status_code == 202
    return response.json()["video_id"]


def test_analysis_completes_all_frames(this_context: ThisContext, video_id: str) -> None:
    status = this_context.client.get(f"/videos/{video_id}/status").json()
    assert status["analyzed_frames"] == status["total_frames"]


def test_first_detection_bbox(this_context: ThisContext, video_id: str) -> None:
    tracks = this_context.client.get(f"/videos/{video_id}/tracks").json()["tracks"]
    assert tracks[0]["detections"][0]["bbox"] == {"center_x": 345, "center_y": 394, "width": 102, "height": 343}
