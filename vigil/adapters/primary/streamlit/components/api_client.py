import httpx

from vigil.adapters.primary.streamlit.components.config import API_BASE_URL, REQUEST_TIMEOUT
from vigil.adapters.primary.streamlit.components.exceptions import (
    VigilAPIError,
    VigilConnectionError,
    VigilNotFoundError,
)
from vigil.adapters.primary.streamlit.components.models import (
    BoundingBox,
    DetectionData,
    TrackData,
    VideoStatus,
)


def _make_client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE_URL, timeout=REQUEST_TIMEOUT)


def upload_video(name: str, data: bytes, *, client: httpx.Client | None = None) -> str:
    """Upload a video file to the backend and return the video_id."""
    _client = client or _make_client()
    try:
        response = _client.post(
            "/analyze-video",
            files={"file": (name, data, "video/mp4")},
        )
        response.raise_for_status()
        return response.json()["video_id"]
    except httpx.ConnectError as error:
        raise VigilConnectionError("Cannot reach the Vigil API. Is the backend running?") from error
    except httpx.TimeoutException as error:
        raise VigilAPIError("Upload request timed out.") from error
    except httpx.HTTPStatusError as error:
        detail = error.response.json().get("detail", str(error))
        raise VigilAPIError(f"Upload failed ({error.response.status_code}): {detail}") from error


def get_status(video_id: str, *, client: httpx.Client | None = None) -> VideoStatus:
    """Fetch the current analysis status for a video."""
    _client = client or _make_client()
    try:
        response = _client.get(f"/videos/{video_id}/status")
        response.raise_for_status()
        payload = response.json()
        return VideoStatus(
            video_id=payload["video_id"],
            analysed_frames=payload["analysed_frames"],
            total_frames=payload["total_frames"],
        )
    except httpx.ConnectError as error:
        raise VigilConnectionError("Cannot reach the Vigil API. Is the backend running?") from error
    except httpx.TimeoutException as error:
        raise VigilAPIError("Status request timed out.") from error
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise VigilNotFoundError(f"Video {video_id} not found.") from error
        detail = error.response.json().get("detail", str(error))
        raise VigilAPIError(f"Status check failed ({error.response.status_code}): {detail}") from error


def get_tracks(video_id: str, *, client: httpx.Client | None = None) -> list[TrackData]:
    """Retrieve all object tracks for a processed video."""
    _client = client or _make_client()
    try:
        response = _client.get(f"/videos/{video_id}/tracks")
        response.raise_for_status()
        payload = response.json()
        return [
            TrackData(
                id=track["id"],
                closed=track["closed"],
                detections=tuple(
                    DetectionData(
                        frame_position=det["frame_position"],
                        label=det["label"],
                        confidence=det["confidence"],
                        bbox=BoundingBox(
                            center_x=det["bbox"]["center_x"],
                            center_y=det["bbox"]["center_y"],
                            width=det["bbox"]["width"],
                            height=det["bbox"]["height"],
                        ),
                    )
                    for det in track["detections"]
                ),
            )
            for track in payload["tracks"]
        ]
    except httpx.ConnectError as error:
        raise VigilConnectionError("Cannot reach the Vigil API. Is the backend running?") from error
    except httpx.TimeoutException as error:
        raise VigilAPIError("Tracks request timed out.") from error
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise VigilNotFoundError(f"Video {video_id} not found.") from error
        detail = error.response.json().get("detail", str(error))
        raise VigilAPIError(f"Tracks retrieval failed ({error.response.status_code}): {detail}") from error
