from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection
from vigil.business_logic.models.frame import FrameId
from vigil.business_logic.models.track import Track, TrackAssignments, TrackId
from vigil.business_logic.services.id_factory import IdFactory
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase

FRAME_ID = FrameId(UUID("8d672f18-906e-4ff9-a06d-938898683720"))


class FakeTracker(Tracker):
    """Implement a tracker for testing purpose."""

    def update(self, tracks: list[Track], detections: list[Detection]) -> TrackAssignments:
        """A track is continued only with identical boxes."""
        matches = [
            (track, detection) for track in tracks for detection in detections if self._is_a_match(track, detection)
        ]
        orphans = list(set(detections) - {match[1] for match in matches})
        return TrackAssignments(orphan_detections=orphans, matches=matches)

    @staticmethod
    def _is_a_match(track: Track, detection: Detection) -> bool:
        return track.detections[-1].bbox == detection.bbox


@dataclass
class ThisContext:
    """Context for testing the tracking use case."""

    detection_repository: InMemoryDetectionRepository
    track_repository: InMemoryTrackRepository
    tracker: FakeTracker
    use_case: TrackObjectsUseCase


@pytest.fixture(scope="function")
def this_context() -> ThisContext:
    detection_repository = InMemoryDetectionRepository()
    track_repository = InMemoryTrackRepository()
    tracker = FakeTracker()
    use_case = TrackObjectsUseCase(
        detection_repository=detection_repository,
        track_repository=track_repository,
        tracker=tracker,
    )
    return ThisContext(
        detection_repository=detection_repository, track_repository=track_repository, tracker=tracker, use_case=use_case
    )


def test_should_start_a_new_track_on_unmatched_detection(this_context: ThisContext):
    # Given
    this_context.detection_repository.save(
        Detection(
            id=UUID("630eb021-73c9-404e-ba8e-000000000000"),
            frame_id=FRAME_ID,
            bbox=BoundingBox(center_x=1, center_y=1, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE),
        )
    )

    # When
    this_context.use_case.execute(frame_id=FRAME_ID)

    # Then
    assert this_context.track_repository.list_tracks() == [
        Track(
            id=TrackId(UUID("e435ff2c-33f4-577e-8a6d-f5a2b04a100b")),
            detections=[
                Detection(
                    id=UUID("630eb021-73c9-404e-ba8e-000000000000"),
                    frame_id=FRAME_ID,
                    bbox=BoundingBox(
                        center_x=1, center_y=1, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE
                    ),
                )
            ],
        ),
    ]


def test_should_extend_a_track_on_matched_detection(this_context: ThisContext):
    # Given
    this_context.detection_repository.save(
        Detection(
            id=UUID("630eb021-73c9-404e-ba8e-000000000001"),
            frame_id=FRAME_ID,
            bbox=BoundingBox(center_x=1, center_y=1, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE),
        )
    )
    first_detection = Detection(
        id=UUID("630eb021-73c9-404e-ba8e-000000000000"),
        frame_id=FrameId(UUID("8d672f18-906e-4ff9-a06d-31f1ee58a170")),
        bbox=BoundingBox(center_x=1, center_y=1, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE),
    )
    this_context.track_repository.save(Track(id=IdFactory.new_track_id(first_detection), detections=[first_detection]))

    # When
    this_context.use_case.execute(frame_id=FRAME_ID)

    # Then
    assert this_context.track_repository.list_tracks() == [
        Track(
            id=TrackId(UUID("4c3757bf-51e9-5e26-8dc4-ceb8e8913641")),
            detections=[
                first_detection,
                Detection(
                    id=UUID("630eb021-73c9-404e-ba8e-000000000001"),
                    frame_id=FRAME_ID,
                    bbox=BoundingBox(
                        center_x=1, center_y=1, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE
                    ),
                ),
            ],
        ),
    ]
