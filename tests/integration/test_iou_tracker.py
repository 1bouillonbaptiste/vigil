from dataclasses import replace
from uuid import UUID

from pytest_cases import parametrize_with_cases

from vigil.adapters.secondary.iou_tracker import IouTracker
from vigil.business_logic.models.detection import BoundingBox, Detection

from tests.helpers import DetectionFactory


class TestIouTrackerCases:
    """Generate cases for test_iou_tracker.

    Each case returns:
    - detections to track
    - the expected aggregated detections
    """

    def case_empty(self):
        return [], [[]]

    def case_single_detection(self):
        factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        detection = factory.create()
        return [detection], [[detection]]

    def case_consecutive_detections(self):
        factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        detections = [factory.create(), factory.create()]
        return detections, [detections]

    def case_several_detections_on_single_frame(self):
        """The tracker consider two tracks on gap."""
        factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        detection = factory.create()
        other = replace(detection, bbox=BoundingBox(center_x=100, center_y=150, width=10, height=30))

        return [detection, other], [[detection], [other]]

    def case_overlaping_tracks(self):
        """There are two tracks starting at different times, but overlapping on a segment."""
        factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        first_track = [
            factory.create(),
            factory.create(),
        ]

        factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"), starting_frame=1)
        second_track = [
            factory.create(bbox=BoundingBox(center_x=100, center_y=150, width=10, height=30)),
            factory.create(bbox=BoundingBox(center_x=100, center_y=150, width=10, height=30)),
        ]

        return first_track + second_track, [first_track, second_track]

    def case_overlaping_and_disjoint_tracks(self):
        """There are two tracks starting at different times, but overlapping on a segment."""
        factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"))
        first_track = [
            factory.create(),
            factory.create(),
        ]

        factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"), starting_frame=1)
        second_track = [
            factory.create(bbox=BoundingBox(center_x=100, center_y=150, width=10, height=30)),
            factory.create(bbox=BoundingBox(center_x=100, center_y=150, width=10, height=30)),
        ]

        factory = DetectionFactory(video_id=UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb"), starting_frame=5)
        third_track = [
            factory.create(bbox=BoundingBox(center_x=100, center_y=150, width=10, height=30)),
            factory.create(bbox=BoundingBox(center_x=100, center_y=150, width=10, height=30)),
        ]

        return first_track + second_track + third_track, [first_track, second_track, third_track]


@parametrize_with_cases("detections, expected_aggregates", cases=TestIouTrackerCases)
def test_can_track_detections_across_frames(detections: list[Detection], expected_aggregates: list[list[Detection]]):
    tracker = IouTracker()
    aggregates = tracker.track(detections)

    assert len(aggregates) == len(expected_aggregates)
    for aggregate, expected in zip(aggregates, expected_aggregates, strict=False):
        assert aggregate == expected
