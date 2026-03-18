from dataclasses import dataclass
from uuid import UUID

import pytest

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.business_logic.gateways.tracker import Tracker
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection
from vigil.business_logic.models.frame import FrameId
from vigil.business_logic.models.track import Track, TrackId
from vigil.business_logic.services.id_factory import IdFactory
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase

VIDEO_ID = UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")
FRAME_ID = FrameId(UUID("8d672f18-906e-4ff9-a06d-938898683720"))
OTHER_FRAME_ID = FrameId(UUID("8d672f18-906e-4ff9-a06d-31f1ee58a170"))
EMPTY_FRAME_ID = FrameId(UUID("00000000-0000-0000-0000-000000000000"))


class FakeTracker(Tracker):
    """Implement a tracker for testing purpose."""

    def update(self, tracks: list[Track], detections: list[Detection]) -> list[tuple[Track, Detection]]:
        """A track is continued only with identical boxes."""
        return [
            (track, detection) for track in tracks for detection in detections if self._is_a_match(track, detection)
        ]

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
        detection_repository=detection_repository,
        track_repository=track_repository,
        tracker=tracker,
        use_case=use_case,
    )


def _detection(detection_id: str, frame_id: FrameId, bbox: BoundingBox) -> Detection:
    return Detection(
        id=UUID(detection_id),
        video_id=VIDEO_ID,
        frame_id=frame_id,
        bbox=bbox,
    )


BBOX = BoundingBox(center_x=1, center_y=1, width=1, height=1, confidence=0.5, label=ClassLabel.PEOPLE)
OTHER_BBOX = BoundingBox(center_x=99, center_y=99, width=10, height=10, confidence=0.5, label=ClassLabel.PEOPLE)


def test_should_start_a_new_track_on_unmatched_detection(this_context: ThisContext):
    # Given
    detection = _detection("630eb021-73c9-404e-ba8e-000000000000", FRAME_ID, BBOX)
    this_context.detection_repository.save(detection)

    # When
    this_context.use_case.execute(frame_id=FRAME_ID, video_id=VIDEO_ID)

    # Then
    assert this_context.track_repository.list_open_tracks(VIDEO_ID) == [
        Track(
            id=TrackId(UUID("e435ff2c-33f4-577e-8a6d-f5a2b04a100b")),
            detections=[detection],
        ),
    ]


def test_should_extend_a_track_on_matched_detection(this_context: ThisContext):
    # Given
    first_detection = _detection("630eb021-73c9-404e-ba8e-000000000000", OTHER_FRAME_ID, BBOX)
    second_detection = _detection("630eb021-73c9-404e-ba8e-000000000001", FRAME_ID, BBOX)
    this_context.track_repository.save(Track(id=IdFactory.new_track_id(first_detection), detections=[first_detection]))
    this_context.detection_repository.save(second_detection)

    # When
    this_context.use_case.execute(frame_id=FRAME_ID, video_id=VIDEO_ID)

    # Then
    assert this_context.track_repository.list_open_tracks(VIDEO_ID) == [
        Track(
            id=TrackId(UUID("4c3757bf-51e9-5e26-8dc4-ceb8e8913641")),
            detections=[first_detection, second_detection],
        ),
    ]


def test_should_close_a_track_after_grace_period_of_missed_frames(this_context: ThisContext):
    # Given: an open track whose bbox never matches the incoming frames
    unmatched_detection = _detection("630eb021-73c9-404e-ba8e-000000000000", OTHER_FRAME_ID, OTHER_BBOX)
    unmatched_track = Track(id=IdFactory.new_track_id(unmatched_detection), detections=[unmatched_detection])
    this_context.track_repository.save(unmatched_track)

    # When: the track is missed for the full grace period
    for _ in range(5):
        this_context.use_case.execute(frame_id=FRAME_ID, video_id=VIDEO_ID)

    # Then
    assert this_context.track_repository.get_by_id(unmatched_track.id).closed is True


def test_should_keep_a_track_open_within_grace_period(this_context: ThisContext):
    # Given
    unmatched_detection = _detection("630eb021-73c9-404e-ba8e-000000000000", OTHER_FRAME_ID, OTHER_BBOX)
    unmatched_track = Track(id=IdFactory.new_track_id(unmatched_detection), detections=[unmatched_detection])
    this_context.track_repository.save(unmatched_track)

    # When: the track is missed but still within the grace period
    for _ in range(4):
        this_context.use_case.execute(frame_id=FRAME_ID, video_id=VIDEO_ID)

    # Then
    assert this_context.track_repository.get_by_id(unmatched_track.id).closed is False


def test_should_reset_grace_period_when_track_is_matched_again(this_context: ThisContext):
    # Given: a track missed 3 times, then matched, then missed 4 more times
    first_detection = _detection("630eb021-73c9-404e-ba8e-000000000000", OTHER_FRAME_ID, BBOX)
    this_context.track_repository.save(Track(id=IdFactory.new_track_id(first_detection), detections=[first_detection]))

    for _ in range(3):
        this_context.use_case.execute(frame_id=EMPTY_FRAME_ID, video_id=VIDEO_ID)

    match_frame = FrameId(UUID("00000000-0000-0000-0000-000000000001"))
    this_context.detection_repository.save(_detection("630eb021-73c9-404e-ba8e-000000000001", match_frame, BBOX))
    this_context.use_case.execute(frame_id=match_frame, video_id=VIDEO_ID)

    for _ in range(4):
        this_context.use_case.execute(frame_id=EMPTY_FRAME_ID, video_id=VIDEO_ID)

    # Then: 4 misses after a match is within the grace period
    assert len(this_context.track_repository.list_open_tracks(VIDEO_ID)) == 1


def test_should_not_mix_tracks_across_videos(this_context: ThisContext):
    # Given: a track belonging to another video
    other_video_id = UUID("ffffffff-0000-0000-0000-000000000000")
    detection = Detection(
        id=UUID("630eb021-73c9-404e-ba8e-000000000000"),
        video_id=other_video_id,
        frame_id=OTHER_FRAME_ID,
        bbox=BBOX,
    )
    this_context.track_repository.save(Track(id=IdFactory.new_track_id(detection), detections=[detection]))

    # When: tracking runs for a different video
    this_context.use_case.execute(frame_id=FRAME_ID, video_id=VIDEO_ID)

    # Then: the other video's track is unaffected
    assert this_context.track_repository.list_open_tracks(VIDEO_ID) == []
    assert len(this_context.track_repository.list_open_tracks(other_video_id)) == 1
