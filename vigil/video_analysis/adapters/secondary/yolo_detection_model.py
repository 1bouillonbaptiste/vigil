from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Final, Protocol

import numpy as np
import numpy.typing as npt
from ultralytics import YOLO

from vigil.video_analysis.business_logic.models.detection import BoundingBox, ClassLabel, Prediction

_MODELS_DIR: Final[Path] = Path(__file__).parent / "models"

_YOLO_CLASS_MAPPING: Final[dict[str, ClassLabel]] = {
    "person": ClassLabel.PERSON,
    "car": ClassLabel.VEHICLE,
    "truck": ClassLabel.VEHICLE,
    "motorcycle": ClassLabel.VEHICLE,
    "bicycle": ClassLabel.VEHICLE,
    "bus": ClassLabel.VEHICLE,
}


class _ScalarTensor(Protocol):
    def item(self) -> float: ...


class _YoloBox(Protocol):
    xyxy: Sequence[Any]
    conf: _ScalarTensor
    cls: _ScalarTensor


class _YoloResult(Protocol):
    boxes: Iterable[_YoloBox]
    names: dict[int, str]


class _YoloModel(Protocol):
    def __call__(self, source: Any, **kwargs: Any) -> list[Any]: ...


class YoloDetectionModel:
    """DetectionModel adapter backed by an Ultralytics YOLO model."""

    def __init__(self, yolo_model: _YoloModel, confidence_threshold: float = 0.5) -> None:
        self._yolo = yolo_model
        self._confidence_threshold = confidence_threshold

    def detect(self, frames: list[npt.NDArray[np.uint8]]) -> list[list[Prediction]]:
        """Run inference on a batch of frames and return domain predictions."""
        results = self._yolo(frames, verbose=False)
        return [
            _extract_predictions(result, frame.shape[0], self._confidence_threshold)
            for result, frame in zip(results, frames, strict=True)
        ]


def _extract_predictions(result: _YoloResult, frame_height: int, confidence_threshold: float) -> list[Prediction]:
    predictions = []
    for box in result.boxes:
        confidence = float(box.conf.item())
        if confidence < confidence_threshold:
            continue
        class_name: str = result.names[int(box.cls.item())]
        label = _YOLO_CLASS_MAPPING.get(class_name)
        if label is None:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        predictions.append(
            Prediction(
                bbox=BoundingBox(
                    center_x=int((x1 + x2) / 2),
                    center_y=frame_height - int((y1 + y2) / 2),
                    width=int(x2 - x1),
                    height=int(y2 - y1),
                ),
                confidence=confidence,
                label=label,
            )
        )
    return predictions


def make_yolo_detection_model(
    model_name: str = "yolov8n",
    confidence_threshold: float = 0.5,
) -> YoloDetectionModel:
    """Wrap a YOLO model as a DetectionModel.

    For plain model names (e.g. ``"yolov8n"``, ``"yolov8s"``), the bundled
    weights under ``models/`` are used when present; otherwise Ultralytics
    downloads and caches them automatically.  Absolute or relative paths are
    forwarded to Ultralytics as-is.
    """
    return YoloDetectionModel(
        yolo_model=YOLO(_resolve_model_source(model_name)), confidence_threshold=confidence_threshold
    )


def _resolve_model_source(model_name: str) -> str:
    """Return the model source string to pass to ``YOLO()``.

    Plain names (no path separator) are resolved against the bundled models
    directory first; if the ``.pt`` file is not found there the name is
    returned unchanged so Ultralytics can handle download/cache.
    """
    if "/" not in model_name and "\\" not in model_name:
        name = model_name.removesuffix(".pt")
        local_path = _MODELS_DIR / f"{name}.pt"
        if local_path.exists():
            return str(local_path)
    return model_name
