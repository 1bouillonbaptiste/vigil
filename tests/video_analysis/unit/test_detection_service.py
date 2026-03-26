from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID

import numpy as np
import numpy.typing as npt
import pytest
from pytest_cases import parametrize_with_cases

from vigil.video_analysis.business_logic.gateways.detection_model import DetectionModel
from vigil.video_analysis.business_logic.models.detection import BoundingBox, ClassLabel, Detection, Prediction
from vigil.video_analysis.business_logic.models.frame import Frame, FrameId
from vigil.video_analysis.business_logic.services.detection_service import DetectionService

VIDEO_ID = UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")
FRAME_ID_0 = FrameId(UUID("8d672f18-906e-4ff9-a06d-938898683720"))
FRAME_ID_1 = FrameId(UUID("8d672f18-906e-4ff9-a06d-938898683721"))


class FakeDetectionModel(DetectionModel):
    """Fake batch detection model.

    Detects a 1x1 bbox at each non-zero pixel in each frame.
    """

    _class_mapping: ClassVar[dict[int, ClassLabel]] = {
        1: ClassLabel.PERSON,
        2: ClassLabel.VEHICLE,
    }

    def detect(self, frames: list[npt.NDArray[np.uint8]]) -> list[list[Prediction]]:
        """Return per-frame predictions."""
        return [self._detect_single(frame) for frame in frames]

    def _detect_single(self, data: npt.NDArray[np.uint8]) -> list[Prediction]:
        num_rows = data.shape[0]
        return [
            Prediction(
                bbox=BoundingBox(
                    center_x=int(col),
                    center_y=int(num_rows - 1 - row),
                    width=1,
                    height=1,
                ),
                confidence=0.5,
                label=label,
            )
            for row, col in np.argwhere(data != 0)
            if (label := self._class_mapping.get(data[row, col].item())) is not None
        ]


@dataclass
class ThisContext:
    """Context for testing DetectionService."""

    detection_model: FakeDetectionModel
    service: DetectionService


@pytest.fixture
def this_context() -> ThisContext:
    detection_model = FakeDetectionModel()
    service = DetectionService(model=detection_model)
    return ThisContext(detection_model=detection_model, service=service)


class ShouldMapBatchOutputToDetectionsCases:
    def case_single_frame_no_detections(self):
        frames = [Frame(id=FRAME_ID_0, position=0, video_id=VIDEO_ID, data=np.array([0, 0], dtype=np.uint8))]
        return frames, []

    def case_single_frame_one_person(self):
        frames = [Frame(id=FRAME_ID_0, position=0, video_id=VIDEO_ID, data=np.array([[1, 0]], dtype=np.uint8))]
        expected = [
            Detection(
                frame_id=FRAME_ID_0,
                frame_position=0,
                prediction=Prediction(
                    bbox=BoundingBox(center_x=0, center_y=0, width=1, height=1),
                    confidence=0.5,
                    label=ClassLabel.PERSON,
                ),
            )
        ]
        return frames, expected

    def case_two_frames_detections_carry_correct_frame_id(self):
        frames = [
            Frame(id=FRAME_ID_0, position=0, video_id=VIDEO_ID, data=np.array([[1, 0]], dtype=np.uint8)),
            Frame(id=FRAME_ID_1, position=1, video_id=VIDEO_ID, data=np.array([[0, 2]], dtype=np.uint8)),
        ]
        expected = [
            Detection(
                frame_id=FRAME_ID_0,
                frame_position=0,
                prediction=Prediction(
                    bbox=BoundingBox(center_x=0, center_y=0, width=1, height=1),
                    confidence=0.5,
                    label=ClassLabel.PERSON,
                ),
            ),
            Detection(
                frame_id=FRAME_ID_1,
                frame_position=1,
                prediction=Prediction(
                    bbox=BoundingBox(center_x=1, center_y=0, width=1, height=1),
                    confidence=0.5,
                    label=ClassLabel.VEHICLE,
                ),
            ),
        ]
        return frames, expected


@parametrize_with_cases("frames, expected_detections", cases=ShouldMapBatchOutputToDetectionsCases)
def test_should_map_batch_output_to_detections(
    this_context: ThisContext, frames: list[Frame], expected_detections: list[Detection]
) -> None:
    # When
    detections = this_context.service.detect(frames)

    # Then
    assert detections == expected_detections
