from typing import Any

import httpx

from vigil.adapters.primary.streamlit.components.config import API_BASE_URL, REQUEST_TIMEOUT
from vigil.adapters.primary.streamlit.components.exceptions import (
    VigilAPIError,
    VigilConnectionError,
    VigilNotFoundError,
)
from vigil.adapters.primary.streamlit.components.mappers import tracks_from_payload, video_status_from_payload
from vigil.adapters.primary.streamlit.components.models import TrackData, VideoStatus


class VigilClient:
    """HTTP client for the Vigil backend API."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    @classmethod
    def default(cls) -> "VigilClient":
        """Build a client pointed at the configured backend URL."""
        return cls(httpx.Client(base_url=API_BASE_URL, timeout=REQUEST_TIMEOUT))

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Send a request and translate httpx errors into Vigil exceptions."""
        try:
            response = self._client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.ConnectError as error:
            raise VigilConnectionError("Cannot reach the Vigil API. Is the backend running?") from error
        except httpx.TimeoutException as error:
            raise VigilAPIError("Request timed out.") from error
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                raise VigilNotFoundError(f"Resource not found: {url}") from error
            detail = error.response.json().get("detail", str(error))
            raise VigilAPIError(f"Request failed ({error.response.status_code}): {detail}") from error

    def upload_video(self, name: str, data: bytes) -> str:
        """Upload a video file to the backend and return the video_id."""
        response = self._request("POST", "/analyze-video", files={"file": (name, data, "video/mp4")})
        return response.json()["video_id"]

    def get_status(self, video_id: str) -> VideoStatus:
        """Fetch the current analysis status for a video."""
        return video_status_from_payload(self._request("GET", f"/videos/{video_id}/status").json())

    def get_tracks(self, video_id: str) -> list[TrackData]:
        """Retrieve all object tracks for a processed video."""
        return tracks_from_payload(self._request("GET", f"/videos/{video_id}/tracks").json())
