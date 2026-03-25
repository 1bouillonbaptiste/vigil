from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

import numpy as np
import numpy.typing as npt
import pytest

from vigil.adapters.secondary.in_memory_analysis_progression_projection import InMemoryAnalysisProgressionProjection
from vigil.business_logic.gateways.video_repository import VideoRepository
from vigil.business_logic.models.frame import Frame, FrameId
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.id_factory import IdFactory
from vigil.business_logic.use_cases.get_analysis_status import GetAnalysisStatusUseCase

VIDEO_ID = IdFactory.new_video_id(VideoSource(uri="test-video"))


class StubVideoRepository(VideoRepository):
    """Controllable video repository for tests."""

    def __init__(self) -> None:
        self.total_frames: int = 0

    def save(self, source: VideoSource, data: bytes) -> None:
        pass

    def read(self, video_id: UUID) -> Iterable[npt.NDArray[np.uint8]]:
        return []

    def frame_count(self, video_id: UUID) -> int:
        return self.total_frames


@dataclass
class ThisContext:
    """Context for testing GetAnalysisStatusUseCase."""

    video_repository: StubVideoRepository
    analysis_progression: InMemoryAnalysisProgressionProjection
    use_case: GetAnalysisStatusUseCase


@pytest.fixture
def this_context() -> ThisContext:
    video_repository = StubVideoRepository()
    analysis_progression = InMemoryAnalysisProgressionProjection()
    use_case = GetAnalysisStatusUseCase(
        video_repository=video_repository,
        analysis_progression=analysis_progression,
    )
    return ThisContext(
        video_repository=video_repository,
        analysis_progression=analysis_progression,
        use_case=use_case,
    )


def _create_frame(position: int) -> Frame:
    return Frame(
        id=FrameId(IdFactory.new_frame_id(video_id=VIDEO_ID, position=position)),
        video_id=VIDEO_ID,
        position=position,
        data=np.array([position], dtype=np.uint8),
    )


def test_should_return_zero_analysed_frames_when_no_frames_stored(this_context: ThisContext) -> None:
    # Given
    this_context.video_repository.total_frames = 5

    # When
    status = this_context.use_case.execute(VIDEO_ID)

    # Then
    assert status.analysed_frames == 0


def test_should_return_analysed_frames_count(this_context: ThisContext) -> None:
    # Given
    this_context.analysis_progression.increment(VIDEO_ID)
    this_context.analysis_progression.increment(VIDEO_ID)
    this_context.analysis_progression.increment(VIDEO_ID)

    # When
    status = this_context.use_case.execute(VIDEO_ID)

    # Then
    assert status.analysed_frames == 3


def test_should_reflect_partial_analysis_progress(this_context: ThisContext) -> None:
    # Given: 3 frames stored out of 10 total
    this_context.video_repository.total_frames = 10
    this_context.analysis_progression.increment(VIDEO_ID)
    this_context.analysis_progression.increment(VIDEO_ID)
    this_context.analysis_progression.increment(VIDEO_ID)

    # When
    status = this_context.use_case.execute(VIDEO_ID)

    # Then
    assert status.analysed_frames == 3
    assert status.total_frames == 10
