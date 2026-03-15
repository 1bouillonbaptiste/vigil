"""Integration tests for YoloDetectionModel.

Requires ultralytics and opencv-python-headless to be installed.
Downloads yolov8n.pt on first run (requires internet access).
"""

from uuid import UUID

import cv2
import numpy as np
import pytest

from vigil.adapters.secondary.yolo_detection_model import YoloDetectionModel
from vigil.business_logic.models.object_class import ObjectClass
from vigil.business_logic.models.raw_frame import RawFrame

VIDEO_ID = UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")


def _make_frame(index: int = 0) -> RawFrame:
    """Create a blank JPEG frame for model smoke-testing."""
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", image)
    return RawFrame(index=index, data=bytes(buffer))


@pytest.mark.integration
def test_model_loads_and_runs_without_error():
    model = YoloDetectionModel()
    frame = _make_frame()

    detections = model.detect(frame, VIDEO_ID)

    # Blank frame may produce zero detections — the important thing is no error.
    assert isinstance(detections, list)


@pytest.mark.integration
def test_detections_have_valid_object_classes():
    model = YoloDetectionModel()
    frame = _make_frame()
    detections = model.detect(frame, VIDEO_ID)

    for detection in detections:
        assert detection.object_class in (ObjectClass.PERSON, ObjectClass.VEHICLE)


@pytest.mark.integration
def test_detections_carry_the_correct_video_id():
    model = YoloDetectionModel()
    frame = _make_frame(index=5)
    detections = model.detect(frame, VIDEO_ID)

    for detection in detections:
        assert detection.video_id == VIDEO_ID
        assert detection.frame_index == 5
