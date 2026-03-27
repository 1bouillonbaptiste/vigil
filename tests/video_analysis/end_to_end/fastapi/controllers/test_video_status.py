import uuid
from pathlib import Path
from uuid import UUID

from starlette.testclient import TestClient

from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.video_analysis.adapters.primary.events_subscriber.frame_detected_subscriber import FrameDetectedSubscriber
from vigil.video_analysis.adapters.primary.fastapi.app_dependencies import (
    _get_analysis_progression,
    _get_detection_model,
    _get_domain_event_publisher,
    _get_track_repository,
    _get_tracker,
    _get_video_repository,
    get_detect_objects_use_case,
)
from vigil.video_analysis.adapters.secondary.fake_detection_model import FakeDetectionModel
from vigil.video_analysis.adapters.secondary.fake_tracker import FakeTracker
from vigil.video_analysis.adapters.secondary.in_memory_analysis_progression_projection import (
    InMemoryAnalysisProgressionProjection,
)
from vigil.video_analysis.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.video_analysis.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.video_analysis.business_logic.models.detection import Detection


class _NoOpDetectObjects:
    """Stub detection use case that publishes no events and returns no
    detections."""

    def execute(self, video_id: UUID) -> list[Detection]:
        return []


def test_returns_frame_counts_after_analysis(fastapi_client: TestClient, tmp_path: Path, fake_video_filepath: Path):
    domain_event_publisher = InMemoryEventPublisher()
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    analysis_progression = InMemoryAnalysisProgressionProjection()

    FrameDetectedSubscriber(publisher=domain_event_publisher, analysis_progression=analysis_progression).subscribe()

    fastapi_client.app.dependency_overrides[_get_domain_event_publisher] = lambda: domain_event_publisher  # type: ignore
    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: video_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_track_repository] = lambda: InMemoryTrackRepository()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_detection_model] = lambda: FakeDetectionModel()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_tracker] = lambda: FakeTracker()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_analysis_progression] = lambda: analysis_progression  # type: ignore

    with open(fake_video_filepath, "rb") as file:
        post_response = fastapi_client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    video_id = post_response.json()["video_id"]
    response = fastapi_client.get(f"/videos/{video_id}/status")

    assert response.status_code == 200
    body = response.json()
    assert body["video_id"] == video_id
    assert body["total_frames"] == 10
    assert body["analyzed_frames"] == 10


def test_returns_zero_analyzed_frames_before_analysis_starts(
    fastapi_client: TestClient, tmp_path: Path, fake_video_filepath: Path
):
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    analysis_progression = InMemoryAnalysisProgressionProjection()

    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: video_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_track_repository] = lambda: InMemoryTrackRepository()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_tracker] = lambda: FakeTracker()  # type: ignore
    fastapi_client.app.dependency_overrides[get_detect_objects_use_case] = lambda: _NoOpDetectObjects()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_analysis_progression] = lambda: analysis_progression  # type: ignore

    with open(fake_video_filepath, "rb") as file:
        post_response = fastapi_client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    video_id = post_response.json()["video_id"]
    response = fastapi_client.get(f"/videos/{video_id}/status")

    assert response.status_code == 200
    assert response.json()["analyzed_frames"] == 0


def test_unknown_video_id_raises_404(fastapi_client: TestClient, tmp_path: Path):
    analysis_progression = InMemoryAnalysisProgressionProjection()

    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: LocalVideoRepository(storage_dir=tmp_path)  # type: ignore
    fastapi_client.app.dependency_overrides[_get_analysis_progression] = lambda: analysis_progression  # type: ignore

    response = fastapi_client.get(f"/videos/{uuid.uuid4()}/status")

    assert response.status_code == 404
