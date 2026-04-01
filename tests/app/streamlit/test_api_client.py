import uuid
from uuid import UUID

import pytest
from starlette.testclient import TestClient

from vigil.app.streamlit.components.api_client import VigilClient
from vigil.app.streamlit.components.exceptions import VigilNotFoundError
from vigil.embedding.adapters.secondary.in_memory_embedded_track_repository import InMemoryEmbeddedTrackRepository
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack, Embedding


def test_upload_video_returns_a_video_id(vigil_client: TestClient, video_bytes: bytes) -> None:
    client = VigilClient(vigil_client)

    video_id = client.upload_video("clip.mp4", video_bytes)

    assert video_id is not None
    assert len(video_id) > 0


def test_get_status_reports_all_frames_analysed_after_upload(vigil_client: TestClient, video_bytes: bytes) -> None:
    client = VigilClient(vigil_client)
    video_id = client.upload_video("clip.mp4", video_bytes)

    status = client.get_status(video_id)

    assert status.analyzed_frames == status.total_frames


def test_get_status_is_complete_after_full_analysis(vigil_client: TestClient, video_bytes: bytes) -> None:
    client = VigilClient(vigil_client)
    video_id = client.upload_video("clip.mp4", video_bytes)

    status = client.get_status(video_id)

    assert status.is_complete is True


def test_get_status_raises_not_found_for_unknown_video(vigil_client: TestClient) -> None:
    client = VigilClient(vigil_client)

    with pytest.raises(VigilNotFoundError):
        client.get_status(str(uuid.uuid4()))


def test_get_tracks_returns_detections_with_integer_frame_position(
    vigil_client: TestClient, video_bytes: bytes
) -> None:
    client = VigilClient(vigil_client)
    video_id = client.upload_video("clip.mp4", video_bytes)

    tracks = client.get_tracks(video_id)

    for track in tracks:
        for detection in track.detections:
            assert isinstance(detection.frame_position, int)


def test_get_tracks_frame_positions_cover_all_frames(vigil_client: TestClient, video_bytes: bytes) -> None:
    client = VigilClient(vigil_client)
    video_id = client.upload_video("clip.mp4", video_bytes)

    tracks = client.get_tracks(video_id)
    positions = {det.frame_position for track in tracks for det in track.detections}

    assert positions == set(range(10))


def test_get_tracks_returns_empty_list_for_unknown_video(vigil_client: TestClient) -> None:
    client = VigilClient(vigil_client)

    assert client.get_tracks(str(uuid.uuid4())) == []


def test_get_tracks_by_description_returns_all_video_tracks_when_description_is_empty(
    vigil_client_with_embedding: TestClient, video_bytes: bytes
) -> None:
    client = VigilClient(vigil_client_with_embedding)
    video_id = client.upload_video("clip.mp4", video_bytes)

    assert client.get_tracks_by_description(video_id, "") == client.get_tracks(video_id)


def test_get_tracks_by_description_returns_intersection_of_video_tracks_and_matching_tracks(
    vigil_client_with_embedding: TestClient,
    video_bytes: bytes,
    embedded_track_repo: InMemoryEmbeddedTrackRepository,
) -> None:
    client = VigilClient(vigil_client_with_embedding)
    video_id = client.upload_video("clip.mp4", video_bytes)

    video_tracks = client.get_tracks(video_id)
    assert len(video_tracks) > 0

    # Register only the first video track in the embedding repo with a matching embedding.
    # (_FakeEmbeddingModel always returns Embedding((0.5, 0.5)), so probability ≈ 1.0.)
    matching_id = UUID(video_tracks[0].id)
    embedded_track_repo.save(EmbeddedTrack(id=matching_id, detections=(Embedding((0.5, 0.5)),)))

    result = client.get_tracks_by_description(video_id, "a person walking")

    assert len(result) == 1
    assert result[0].id == str(matching_id)
    assert result[0].match_score is not None
    assert result[0].match_score > 0.9
