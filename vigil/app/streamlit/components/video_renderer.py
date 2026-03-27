import tempfile
from collections import defaultdict
from pathlib import Path

import cv2
import imageio
import numpy as np

from vigil.app.streamlit.components.models import DetectionData, TrackData

_LABEL_COLORS: dict[str, tuple[int, int, int]] = {
    "person": (50, 205, 50),  # lime green
    "vehicle": (30, 144, 255),  # dodger blue
}
_DEFAULT_COLOR: tuple[int, int, int] = (200, 200, 200)

_BOX_THICKNESS = 2
_FONT = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE = 0.55
_FONT_THICKNESS = 1


def _build_frame_detections(tracks: list[TrackData]) -> dict[int, list[DetectionData]]:
    """Group detections by frame position across all tracks."""
    by_position: dict[int, list[DetectionData]] = defaultdict(list)
    for track in tracks:
        for detection in track.detections:
            by_position[detection.frame_position].append(detection)
    return dict(by_position)


def _draw_detections(frame: np.ndarray, detections: list[DetectionData]) -> np.ndarray:
    """Draw bounding boxes and labels on a single frame (returns a copy)."""
    output = frame.copy()
    frame_height = frame.shape[0]
    for det in detections:
        b = det.bbox
        x1 = b.center_x - b.width // 2
        y1 = frame_height - (b.center_y + b.height // 2)
        x2 = b.center_x + b.width // 2
        y2 = frame_height - (b.center_y - b.height // 2)

        color = _LABEL_COLORS.get(det.label, _DEFAULT_COLOR)
        cv2.rectangle(output, (x1, y1), (x2, y2), color, _BOX_THICKNESS)

        label_text = f"{det.label} {det.confidence:.0%}"
        (text_w, text_h), baseline = cv2.getTextSize(label_text, _FONT, _FONT_SCALE, _FONT_THICKNESS)
        cv2.rectangle(output, (x1, y1 - text_h - baseline - 4), (x1 + text_w + 4, y1), color, -1)
        cv2.putText(
            output,
            label_text,
            (x1 + 2, y1 - baseline - 2),
            _FONT,
            _FONT_SCALE,
            (255, 255, 255),
            _FONT_THICKNESS,
            cv2.LINE_AA,
        )
    return output


def render_video_with_tracks(video_path: Path, tracks: list[TrackData]) -> Path:
    """Render a video with bounding boxes drawn for each tracked object.

    Writes the annotated video to a temporary file and returns its path. The
    caller is responsible for cleaning up the file when done.
    """
    frame_detections = _build_frame_detections(tracks)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_tmp:
        output_path = output_tmp.name

    writer = imageio.get_writer(
        output_path,
        fps=fps,
        codec="libx264",
        pixelformat="yuv420p",
        macro_block_size=1,
        output_params=["-movflags", "+faststart"],
    )

    position = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        detections = frame_detections.get(position, [])
        annotated = _draw_detections(frame, detections)
        writer.append_data(annotated[:, :, ::-1])  # BGR → RGB
        position += 1

    cap.release()
    writer.close()

    return Path(output_path)
