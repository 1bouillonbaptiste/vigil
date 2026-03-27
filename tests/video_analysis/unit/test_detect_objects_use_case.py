from collections.abc import Iterable
from uuid import UUID

import numpy as np
import numpy.typing as npt
import pytest

from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.video_analysis.business_logic.gateways.detection_model import DetectionModel
from vigil.video_analysis.business_logic.models.detection import Prediction
from vigil.video_analysis.business_logic.models.frame_detected import FrameDetected
from vigil.video_analysis.business_logic.models.video_source import VideoSource
from vigil.video_analysis.business_logic.services.id_factory import IdFactory
from vigil.video_analysis.business_logic.use_cases.detect_objects import DetectObjectsUseCase

VIDEO_ID = IdFactory.new_video_id(VideoSource(uri="test-video"))


class StubVideoRepository:
    def __init__(self) -> None:
        self._frames: list[npt.NDArray[np.uint8]] = []

    def add(self, data: npt.NDArray[np.uint8]) -> None:
        self._frames.append(data)

    def save(self, source: object, data: bytes) -> None:
        pass

    def read(self, video_id: UUID) -> Iterable[npt.NDArray[np.uint8]]:
        return self._frames

    def frame_count(self, video_id: UUID) -> int:
        return len(self._frames)


class SpyDetectionModel(DetectionModel):
    def __init__(self) -> None:
        self.call_count = 0

    def detect(self, frames: list[npt.NDArray[np.uint8]]) -> list[list[Prediction]]:
        self.call_count += 1
        return [[] for _ in frames]


class SpyFrameDetected:
    def __init__(self) -> None:
        self._events: list[FrameDetected] = []

    def __call__(self, event: FrameDetected) -> None:
        self._events.append(event)

    def to_list(self) -> list[FrameDetected]:
        return self._events.copy()


@pytest.mark.parametrize(
    "n_frames,batch_size,expected_model_calls",
    [
        (2, 2, 1),  # exact batch: model called once
        (3, 2, 2),  # partial batch: model called twice
    ],
)
def test_should_batch_detection(n_frames: int, batch_size: int, expected_model_calls: int) -> None:
    video_repository = StubVideoRepository()
    for _ in range(n_frames):
        video_repository.add(np.array([1], dtype=np.uint8))

    spy_model = SpyDetectionModel()
    domain_event_publisher = InMemoryEventPublisher()
    frame_detected_events = SpyFrameDetected()
    domain_event_publisher.subscribe(handler=frame_detected_events)

    use_case = DetectObjectsUseCase(
        domain_event_publisher=domain_event_publisher,
        video_repository=video_repository,
        detection_model=spy_model,
        batch_size=batch_size,
    )
    use_case.execute(VIDEO_ID)

    assert spy_model.call_count == expected_model_calls
    assert len(frame_detected_events.to_list()) == n_frames
