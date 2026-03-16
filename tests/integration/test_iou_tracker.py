from uuid import UUID

from pytest_cases import parametrize_with_cases

from vigil.adapters.secondary.in_memory_frame_repository import InMemoryFrameRepository
from vigil.adapters.secondary.iou_tracker import IouTracker
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection

from tests.helpers import DetectionFactory


class TestIouTrackerCases:
    """Generate cases for test_iou_tracker.

    Each case returns:
    - detections to track
    - the expected aggregated detections
    - the frame repository used to create the detections
    """

    def case_empty(self):
        frame_repository = InMemoryFrameRepository()
        return [], [[]], frame_repository

    def case_single_detection(self):
        frame_repository = InMemoryFrameRepository()
        factory = DetectionFactory(frame_repository=frame_repository)
        factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        detection = factory.create(at_position=0)
        return [detection], [[detection]], frame_repository

    def case_consecutive_detections(self):
        frame_repository = InMemoryFrameRepository()
        factory = DetectionFactory(frame_repository=frame_repository)
        factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        detections = [factory.create(at_position=0), factory.create(at_position=1)]
        return detections, [detections], frame_repository

    def case_several_detections_on_single_frame(self):
        """The tracker consider two tracks on gap."""
        frame_repository = InMemoryFrameRepository()
        factory = DetectionFactory(frame_repository=frame_repository)
        factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        detection = factory.create(at_position=0)
        other = factory.create(
            bbox=BoundingBox(center_x=100, center_y=150, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE),
            at_position=0,
        )

        return [detection, other], [[detection], [other]], frame_repository

    def case_overlaping_tracks(self):
        """There are two tracks starting at different times, but overlapping on a segment."""
        frame_repository = InMemoryFrameRepository()
        factory = DetectionFactory(frame_repository=frame_repository)
        factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        first_track = [
            factory.create(at_position=0),
            factory.create(at_position=1),
        ]
        second_track = [
            factory.create(
                bbox=BoundingBox(
                    center_x=100, center_y=150, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE
                ),
                at_position=1,
            ),
            factory.create(
                bbox=BoundingBox(
                    center_x=100, center_y=150, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE
                ),
                at_position=2,
            ),
        ]

        return first_track + second_track, [first_track, second_track], frame_repository

    def case_overlaping_and_disjoint_tracks(self):
        """There are two tracks starting at different times, but overlapping on a segment."""
        frame_repository = InMemoryFrameRepository()
        factory = DetectionFactory(frame_repository=frame_repository)
        factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        first_track = [
            factory.create(at_position=0),
            factory.create(at_position=1),
        ]
        second_track = [
            factory.create(
                bbox=BoundingBox(
                    center_x=100, center_y=150, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE
                ),
                at_position=1,
            ),
            factory.create(
                bbox=BoundingBox(
                    center_x=100, center_y=150, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE
                ),
                at_position=2,
            ),
        ]
        third_track = [
            factory.create(
                bbox=BoundingBox(
                    center_x=100, center_y=150, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE
                ),
                at_position=5,
            ),
            factory.create(
                bbox=BoundingBox(
                    center_x=100, center_y=150, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE
                ),
                at_position=6,
            ),
        ]

        return first_track + second_track + third_track, [first_track, second_track, third_track], frame_repository


@parametrize_with_cases("detections, expected_aggregates, frame_repository", cases=TestIouTrackerCases)
def test_can_track_detections_across_frames(
    detections: list[Detection],
    expected_aggregates: list[list[Detection]],
    frame_repository: InMemoryFrameRepository,
):
    tracker = IouTracker(frame_repository=frame_repository)
    aggregates = tracker.track(detections)

    assert len(aggregates) == len(expected_aggregates)
    for aggregate, expected in zip(aggregates, expected_aggregates, strict=False):
        assert aggregate == expected


def test_should_split_tracks_when_iou_is_below_min_iou():
    # IoU between these two boxes ≈ 0.43
    frame_repository = InMemoryFrameRepository()
    factory = DetectionFactory(frame_repository=frame_repository)
    factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    detection1 = factory.create(
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE),
        at_position=0,
    )
    detection2 = factory.create(
        bbox=BoundingBox(center_x=104, center_y=50, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE),
        at_position=1,
    )

    tracker = IouTracker(frame_repository=frame_repository, min_iou=0.5)
    tracks = tracker.track([detection1, detection2])

    assert len(tracks) == 2
    assert tracks[0] == [detection1]
    assert tracks[1] == [detection2]


def test_should_keep_track_when_iou_is_above_min_iou():
    # IoU between these two boxes ≈ 0.43
    frame_repository = InMemoryFrameRepository()
    factory = DetectionFactory(frame_repository=frame_repository)
    factory.with_video(UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
    detection1 = factory.create(
        bbox=BoundingBox(center_x=100, center_y=50, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE),
        at_position=0,
    )
    detection2 = factory.create(
        bbox=BoundingBox(center_x=104, center_y=50, width=10, height=30, confidence=0.8, label=ClassLabel.PEOPLE),
        at_position=1,
    )

    tracker = IouTracker(frame_repository=frame_repository, min_iou=0.4)
    tracks = tracker.track([detection1, detection2])

    assert len(tracks) == 1
    assert tracks[0] == [detection1, detection2]
