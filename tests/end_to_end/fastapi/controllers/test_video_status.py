import uuid
from pathlib import Path
from uuid import UUID

from starlette.testclient import TestClient
from vigil.adapters.secondary.in_memory_domain_event_publisher import InMemoryDomainEventPublisher

from vigil.adapters.primary.fastapi.app_dependencies import (
    _get_detection_model,
    _get_progress_projection,
    _get_publisher,
    _get_track_repository,
    _get_tracker,
    _get_video_repository,
    get_video_analysis_workflow,
)
from vigil.adapters.secondary.fake_detection_model import FakeDetectionModel
from vigil.adapters.secondary.fake_tracker import FakeTracker
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.local_video_repository import LocalVideoRepository
from vigil.business_logic.models.frame_analyzed import FrameAnalyzed
from vigil.business_logic.services.analysis_progress_projection import AnalysisProgressProjection


class _NoOpWorkflow:
    """Dummy workflow that does nothing."""

    def execute(self, video_id: UUID) -> None:
        """Not publishing events makes the analysis appear pending."""
        pass


def test_returns_frame_counts_after_analysis(fastapi_client: TestClient, tmp_path: Path, fake_video_filepath: Path):
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    publisher: InMemoryDomainEventPublisher[FrameAnalyzed] = InMemoryDomainEventPublisher()
    progress_projection = AnalysisProgressProjection()
    publisher.subscribe(progress_projection)

    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: video_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_publisher] = lambda: publisher  # type: ignore
    fastapi_client.app.dependency_overrides[_get_progress_projection] = lambda: progress_projection  # type: ignore
    fastapi_client.app.dependency_overrides[_get_track_repository] = lambda: InMemoryTrackRepository()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_detection_model] = lambda: FakeDetectionModel()  # type: ignore
    fastapi_client.app.dependency_overrides[_get_tracker] = lambda: FakeTracker()  # type: ignore

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
    video_repository = LocalVideoRepository(storage_dir=tmp_path)
    progress_projection = AnalysisProgressProjection()

    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: video_repository  # type: ignore
    fastapi_client.app.dependency_overrides[_get_progress_projection] = lambda: progress_projection  # type: ignore
    fastapi_client.app.dependency_overrides[get_video_analysis_workflow] = lambda: _NoOpWorkflow()  # type: ignore

    with open(fake_video_filepath, "rb") as file:
        post_response = fastapi_client.post("/analyze-video", files={"file": ("video.mp4", file, "video/mp4")})

    video_id = post_response.json()["video_id"]
    response = fastapi_client.get(f"/videos/{video_id}/status")

    assert response.status_code == 200
    assert response.json()["analysed_frames"] == 0


def test_unknown_video_id_raises_404(fastapi_client: TestClient, tmp_path: Path):
    fastapi_client.app.dependency_overrides[_get_video_repository] = lambda: LocalVideoRepository(storage_dir=tmp_path)  # type: ignore
    fastapi_client.app.dependency_overrides[_get_progress_projection] = lambda: AnalysisProgressProjection()  # type: ignore

    response = fastapi_client.get(f"/videos/{uuid.uuid4()}/status")

    assert response.status_code == 404
