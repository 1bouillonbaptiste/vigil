import uuid
from pathlib import Path
from uuid import UUID

from starlette.testclient import TestClient

from vigil.adapters.primary.events_subscriber.frame_analyzed_subscriber import FrameAnalyzedSubscriber
from vigil.adapters.primary.fastapi.app_dependencies import (
    _get_analysis_progression,
    _get_detection_model,
    _get_domain_event_publisher,
    _get_frame_repository,
    _get_track_repository,
    _get_tracker,
    _get_video_repository,
    get_video_analysis_workflow,
)
from vigil.adapters.secondary.fake_detection_model import FakeDetectionModel
from vigil.adapters.secondary.fake_tracker import FakeTracker
from vigil.adapters.secondary.in_memory_analysis_progression_projection import InMemoryAnalysisProgressionProjection
from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher


class _NoOpWorkflow:
    """Dummy workflow that does nothing."""

    def execute(self, video_id: UUID) -> None:
        """Not saving analyzed frames make the analysis think the video is
        pending."""
        pass


def test_returns_frame_counts_after_analysis(fastapi_client: TestClient, tmp_path: Path, fake_video_filepath: Path):
    domain_event_publisher = InMemoryEventPublisher()
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    frame_repository = InMemoryFrameRepository()
    analysis_progression = InMemoryAnalysisProgressionProjection()

    FrameAnalyzedSubscriber(publisher=domain_event_publisher, analysis_progression=analysis_progression).subscribe()

    fastapi_client.app.dependency_overrides[_get_domain_event_publisher] = lambda: domain_event_publisher  # type: ignore
    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: video_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_frame_repository] = lambda: frame_repository  # type: ignore
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
    assert body["analysed_frames"] == 10


def test_returns_zero_analysed_frames_before_analysis_starts(
    fastapi_client: TestClient, tmp_path: Path, fake_video_filepath: Path
):
    domain_event_publisher = InMemoryEventPublisher()
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    frame_repository = InMemoryFrameRepository()
    analysis_progression = InMemoryAnalysisProgressionProjection()

    FrameAnalyzedSubscriber(publisher=domain_event_publisher, analysis_progression=analysis_progression).subscribe()

    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: video_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_frame_repository] = lambda: frame_repository  # type: ignore
    fastapi_client.app.dependency_overrides[get_video_analysis_workflow] = lambda: _NoOpWorkflow()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_analysis_progression] = lambda: analysis_progression  # type: ignore

    with open(fake_video_filepath, "rb") as file:
        post_response = fastapi_client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    video_id = post_response.json()["video_id"]
    response = fastapi_client.get(f"/videos/{video_id}/status")

    assert response.status_code == 200
    assert response.json()["analysed_frames"] == 0


def test_unknown_video_id_raises_404(fastapi_client: TestClient, tmp_path: Path):
    domain_event_publisher = InMemoryEventPublisher()
    analysis_progression = InMemoryAnalysisProgressionProjection()

    FrameAnalyzedSubscriber(publisher=domain_event_publisher, analysis_progression=analysis_progression).subscribe()

    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: LocalVideoRepository(storage_dir=tmp_path)  # type: ignore
    fastapi_client.app.dependency_overrides[_get_frame_repository] = lambda: InMemoryFrameRepository()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_analysis_progression] = lambda: analysis_progression  # type: ignore

    response = fastapi_client.get(f"/videos/{uuid.uuid4()}/status")

    assert response.status_code == 404
