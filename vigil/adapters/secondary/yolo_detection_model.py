from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Final, Protocol

import numpy as np
import numpy.typing as npt

from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Prediction

_MODELS_DIR: Final[Path] = Path(__file__).parent / "models"
_DEFAULT_MODEL: Final[Path] = _MODELS_DIR / "yolov8n.pt"

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
    model_path: Path = _DEFAULT_MODEL,
    confidence_threshold: float = 0.5,
) -> YoloDetectionModel:
    """Load a YOLO model from disk and wrap it as a DetectionModel.

    Defaults to the bundled yolov8n weights at ``models/yolov8n.pt``.
    Pass a different ``model_path`` to swap variants without a code change.
    """
    from ultralytics import YOLO

    return YoloDetectionModel(yolo_model=YOLO(str(model_path)), confidence_threshold=confidence_threshold)
