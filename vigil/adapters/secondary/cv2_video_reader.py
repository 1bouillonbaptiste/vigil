from typing import Iterator

import cv2

from vigil.business_logic.gateways.video_reader import VideoDurationExceededError
from vigil.business_logic.models.raw_frame import RawFrame

_MAX_DURATION_SECONDS = 300  # 5 minutes


class Cv2VideoReader:
    """Read video frames using OpenCV, with duration validation and frame sampling."""

    def read(self, video_path: str, frame_interval: int = 5) -> Iterator[RawFrame]:
        """Yield JPEG-encoded frames sampled every frame_interval frames.

        Raises:
            FileNotFoundError: If the video cannot be opened.
            VideoDurationExceededError: If the video exceeds 5 minutes.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video file: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if fps > 0 and total_frames > 0:
                duration_seconds = total_frames / fps
                if duration_seconds > _MAX_DURATION_SECONDS:
                    raise VideoDurationExceededError(
                        f"Video duration {duration_seconds:.0f}s exceeds the {_MAX_DURATION_SECONDS // 60}-minute limit"
                    )

            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_index % frame_interval == 0:
                    _, buffer = cv2.imencode(".jpg", frame)
                    yield RawFrame(index=frame_index, data=bytes(buffer))
                frame_index += 1
        finally:
            cap.release()
