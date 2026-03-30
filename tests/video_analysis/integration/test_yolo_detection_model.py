from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt
import pytest
from pytest_cases import parametrize_with_cases

from vigil.shared_kernel.models.image import Image
from vigil.video_analysis.adapters.secondary.yolo_detection_model import YoloDetectionModel, make_yolo_detection_model
from vigil.video_analysis.business_logic.models.detection import BoundingBox, ClassLabel

# ---------------------------------------------------------------------------
# Fake YOLO infrastructure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FakeBox:
    """Minimal stand-in for an ultralytics Boxes single-detection object."""

    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    cls_idx: int

    @property
    def xyxy(self) -> list[npt.NDArray[np.float32]]:
        return [np.array([self.x1, self.y1, self.x2, self.y2], dtype=np.float32)]

    @property
    def conf(self) -> np.float32:
        return np.float32(self.confidence)

    @property
    def cls(self) -> np.float32:
        return np.float32(self.cls_idx)


@dataclass
class FakeYoloResult:
    """Minimal stand-in for an ultralytics Results object."""

    boxes: list[FakeBox]
    names: dict[int, str]


@dataclass
class FakeYoloModel:
    """Fake YOLO callable that returns pre-defined results."""

    results: list[FakeYoloResult]

    def __call__(self, source: Any, **kwargs: Any) -> list[FakeYoloResult]:
        return self.results


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def make_frame(height: int = 100, width: int = 100) -> Image:
    return Image(np.zeros((height, width, 3), dtype=np.uint8))


def make_fake_box(
    x1: float = 10.0,
    y1: float = 20.0,
    x2: float = 30.0,
    y2: float = 40.0,
    confidence: float = 0.9,
    cls_idx: int = 0,
) -> FakeBox:
    return FakeBox(x1=x1, y1=y1, x2=x2, y2=y2, confidence=confidence, cls_idx=cls_idx)


# ---------------------------------------------------------------------------
# Tests — class name mapping
# ---------------------------------------------------------------------------


class ShouldMapYoloClassesToDomainLabelsCases:
    def case_person(self) -> tuple[str, ClassLabel]:
        return "person", ClassLabel.PERSON

    def case_car(self) -> tuple[str, ClassLabel]:
        return "car", ClassLabel.VEHICLE

    def case_truck(self) -> tuple[str, ClassLabel]:
        return "truck", ClassLabel.VEHICLE

    def case_motorcycle(self) -> tuple[str, ClassLabel]:
        return "motorcycle", ClassLabel.VEHICLE

    def case_bicycle(self) -> tuple[str, ClassLabel]:
        return "bicycle", ClassLabel.VEHICLE

    def case_bus(self) -> tuple[str, ClassLabel]:
        return "bus", ClassLabel.VEHICLE


@parametrize_with_cases("class_name, expected_label", cases=ShouldMapYoloClassesToDomainLabelsCases)
def test_should_map_yolo_class_to_domain_label(class_name: str, expected_label: ClassLabel) -> None:
    box = make_fake_box(cls_idx=0)
    yolo = FakeYoloModel(results=[FakeYoloResult(boxes=[box], names={0: class_name})])
    model = YoloDetectionModel(yolo_model=yolo, confidence_threshold=0.0)

    result = model.detect([make_frame()])

    assert len(result[0]) == 1
    assert result[0][0].label == expected_label


def test_should_silently_drop_unknown_classes() -> None:
    box = make_fake_box(cls_idx=0)
    yolo = FakeYoloModel(results=[FakeYoloResult(boxes=[box], names={0: "cat"})])
    model = YoloDetectionModel(yolo_model=yolo, confidence_threshold=0.0)

    result = model.detect([make_frame()])

    assert result == [[]]


# ---------------------------------------------------------------------------
# Tests — bounding box conversion
# ---------------------------------------------------------------------------


def test_should_convert_xyxy_to_center_coords_with_y_flip() -> None:
    # Frame height = 100
    # YOLO xyxy (top-left origin): x1=10, y1=20, x2=30, y2=40
    # Expected domain BoundingBox (bottom-left origin):
    #   center_x = (10+30)/2 = 20
    #   center_y = 100 - (20+40)/2 = 100 - 30 = 70
    #   width = 30-10 = 20, height = 40-20 = 20
    box = make_fake_box(x1=10.0, y1=20.0, x2=30.0, y2=40.0, cls_idx=0)
    yolo = FakeYoloModel(results=[FakeYoloResult(boxes=[box], names={0: "person"})])
    model = YoloDetectionModel(yolo_model=yolo, confidence_threshold=0.0)

    result = model.detect([make_frame(height=100)])

    assert result[0][0].bbox == BoundingBox(center_x=20, center_y=70, width=20, height=20)


# ---------------------------------------------------------------------------
# Tests — confidence threshold
# ---------------------------------------------------------------------------


def test_should_drop_predictions_below_confidence_threshold() -> None:
    low = make_fake_box(confidence=0.3, cls_idx=0)
    high = make_fake_box(confidence=0.8, cls_idx=0)
    yolo = FakeYoloModel(results=[FakeYoloResult(boxes=[low, high], names={0: "person"})])
    model = YoloDetectionModel(yolo_model=yolo, confidence_threshold=0.5)

    result = model.detect([make_frame()])

    assert len(result[0]) == 1
    assert result[0][0].confidence == pytest.approx(0.8)


def test_should_keep_predictions_at_confidence_threshold() -> None:
    box = make_fake_box(confidence=0.5, cls_idx=0)
    yolo = FakeYoloModel(results=[FakeYoloResult(boxes=[box], names={0: "person"})])
    model = YoloDetectionModel(yolo_model=yolo, confidence_threshold=0.5)

    result = model.detect([make_frame()])

    assert len(result[0]) == 1


# ---------------------------------------------------------------------------
# Tests — batch alignment
# ---------------------------------------------------------------------------


def test_should_return_one_prediction_list_per_frame() -> None:
    box = make_fake_box(cls_idx=0)
    yolo = FakeYoloModel(
        results=[
            FakeYoloResult(boxes=[box], names={0: "person"}),
            FakeYoloResult(boxes=[], names={}),
        ]
    )
    model = YoloDetectionModel(yolo_model=yolo, confidence_threshold=0.0)

    result = model.detect([make_frame(), make_frame()])

    assert len(result) == 2
    assert len(result[0]) == 1
    assert len(result[1]) == 0


# ---------------------------------------------------------------------------
# Tests — factory
# ---------------------------------------------------------------------------


def test_should_build_detection_model_from_bundled_weights() -> None:
    model = make_yolo_detection_model()

    assert isinstance(model, YoloDetectionModel)
