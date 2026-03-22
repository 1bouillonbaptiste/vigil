import uuid

import pytest
from starlette.testclient import TestClient

from vigil.adapters.primary.streamlit.components.api_client import get_status, get_tracks, upload_video
from vigil.adapters.primary.streamlit.components.exceptions import VigilNotFoundError


def test_upload_video_returns_a_video_id(vigil_client: TestClient, video_bytes: bytes) -> None:
    video_id = upload_video("clip.mp4", video_bytes, client=vigil_client)

    assert video_id is not None
    assert len(video_id) > 0


def test_get_status_reports_all_frames_analysed_after_upload(vigil_client: TestClient, video_bytes: bytes) -> None:
    video_id = upload_video("clip.mp4", video_bytes, client=vigil_client)

    status = get_status(video_id, client=vigil_client)

    assert status.analysed_frames == status.total_frames


def test_get_status_is_complete_after_full_analysis(vigil_client: TestClient, video_bytes: bytes) -> None:
    video_id = upload_video("clip.mp4", video_bytes, client=vigil_client)

    status = get_status(video_id, client=vigil_client)

    assert status.is_complete is True


def test_get_status_raises_not_found_for_unknown_video(vigil_client: TestClient) -> None:
    with pytest.raises(VigilNotFoundError):
        get_status(str(uuid.uuid4()), client=vigil_client)


def test_get_tracks_returns_detections_with_integer_frame_position(
    vigil_client: TestClient, video_bytes: bytes
) -> None:
    video_id = upload_video("clip.mp4", video_bytes, client=vigil_client)

    tracks = get_tracks(video_id, client=vigil_client)

    for track in tracks:
        for detection in track.detections:
            assert isinstance(detection.frame_position, int)


def test_get_tracks_frame_positions_cover_all_frames(vigil_client: TestClient, video_bytes: bytes) -> None:
    video_id = upload_video("clip.mp4", video_bytes, client=vigil_client)

    tracks = get_tracks(video_id, client=vigil_client)
    positions = {det.frame_position for track in tracks for det in track.detections}

    assert positions == set(range(10))


def test_get_tracks_returns_empty_list_for_unknown_video(vigil_client: TestClient) -> None:
    tracks = get_tracks(str(uuid.uuid4()), client=vigil_client)

    assert tracks == []
