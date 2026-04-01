from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from vigil.monitoring.adapters.secondary.in_memory_analysis_job_repository import InMemoryAnalysisJobRepository
from vigil.monitoring.business_logic.models.analysis_job import AnalysisJob
from vigil.monitoring.business_logic.use_cases.get_analysis_status import GetAnalysisStatusUseCase

VIDEO_ID: UUID = uuid4()


@dataclass
class ThisContext:
    repository: InMemoryAnalysisJobRepository
    use_case: GetAnalysisStatusUseCase


@pytest.fixture
def this_context() -> ThisContext:
    repository = InMemoryAnalysisJobRepository()
    use_case = GetAnalysisStatusUseCase(analysis_job_repository=repository)
    return ThisContext(repository=repository, use_case=use_case)


def test_should_return_zero_analyzed_frames_for_new_job(this_context: ThisContext) -> None:
    # Given
    this_context.repository.create(AnalysisJob(video_id=VIDEO_ID, total_frames=10))

    # When
    status = this_context.use_case.execute(VIDEO_ID)

    # Then
    assert status.analyzed_frames == 0
    assert status.total_frames == 10


def test_should_reflect_analyzed_frames(this_context: ThisContext) -> None:
    # Given
    job = AnalysisJob(video_id=VIDEO_ID, total_frames=10, analyzed_frames=5)
    this_context.repository.create(job)

    # When
    status = this_context.use_case.execute(VIDEO_ID)

    # Then
    assert status.analyzed_frames == 5
