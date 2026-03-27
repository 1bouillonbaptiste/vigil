from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from vigil.video_analysis.adapters.primary.fastapi.app_dependencies import _get_detection_model
from vigil.video_analysis.adapters.primary.fastapi.main import app
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


def test_should_detect_people_across_video_frames(this_context: ThisContext, realistic_video_filepath: Path) -> None:
    with open(realistic_video_filepath, "rb") as f:
        post_response = this_context.client.post(
            "/analyze-video",
            files={"file": (realistic_video_filepath.name, f, "video/mp4")},
        )
    assert post_response.status_code == 202
    video_id = post_response.json()["video_id"]

    status_response = this_context.client.get(f"/videos/{video_id}/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["analyzed_frames"] == status["total_frames"]

    response = this_context.client.get(f"/videos/{video_id}/tracks")

    assert response.status_code == 200
    tracks = response.json()["tracks"]
    all_detections = [detection for track in tracks for detection in track["detections"]]
    labels = {detection["label"] for detection in all_detections}
    assert labels == {"person"}

    assert all_detections[0]["bbox"] == {"center_x": 345, "center_y": 394, "width": 102, "height": 343}
