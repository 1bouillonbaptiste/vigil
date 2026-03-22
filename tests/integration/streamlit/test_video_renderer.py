from pathlib import Path

import cv2
from starlette.testclient import TestClient

from vigil.adapters.primary.streamlit.components.api_client import VigilClient
from vigil.adapters.primary.streamlit.components.video_renderer import render_video_with_tracks

from tests.integration.streamlit.conftest import make_detection, make_track


def test_renders_a_readable_mp4_file(video_path: Path) -> None:
    output = render_video_with_tracks(video_path, tracks=[])

    cap = cv2.VideoCapture(str(output))
    assert cap.isOpened()
    cap.release()
    output.unlink(missing_ok=True)


def test_output_has_same_frame_count_as_input(video_path: Path) -> None:
    output = render_video_with_tracks(video_path, tracks=[])

    cap = cv2.VideoCapture(str(output))
    frame_count = 0
    while cap.read()[0]:
        frame_count += 1
    cap.release()
    output.unlink(missing_ok=True)

    assert frame_count == 10


def test_renders_without_error_when_detections_span_all_frames(video_path: Path) -> None:
    tracks = [
        make_track(
            detections=tuple(make_detection(frame_position=i) for i in range(10)),
        )
    ]

    output = render_video_with_tracks(video_path, tracks=tracks)

    assert output.exists()
    output.unlink(missing_ok=True)


def test_renders_bboxes_from_real_analysis(vigil_client: TestClient, video_path: Path, video_bytes: bytes) -> None:
    client = VigilClient(vigil_client)
    video_id = client.upload_video("clip.mp4", video_bytes)
    tracks = client.get_tracks(video_id)

    output = render_video_with_tracks(video_path, tracks=tracks)

    cap = cv2.VideoCapture(str(output))
    frame_count = 0
    while cap.read()[0]:
        frame_count += 1
    cap.release()
    output.unlink(missing_ok=True)

    assert frame_count == 10
