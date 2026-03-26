from uuid import UUID

from vigil.video_analysis.adapters.secondary.bytetrack_tracker import ByteTrackTracker, make_bytetrack_tracker
from vigil.video_analysis.business_logic.models.detection import BoundingBox, ClassLabel, Detection, Prediction
from vigil.video_analysis.business_logic.models.frame import FrameId

FRAME_0_ID = FrameId(UUID("00000000-0000-0000-0000-000000000000"))
FRAME_1_ID = FrameId(UUID("00000000-0000-0000-0000-000000000001"))
FRAME_2_ID = FrameId(UUID("00000000-0000-0000-0000-000000000002"))

BBOX_A = BoundingBox(center_x=100, center_y=100, width=60, height=60)
BBOX_A_NEARBY = BoundingBox(center_x=102, center_y=102, width=60, height=60)
BBOX_B = BoundingBox(center_x=400, center_y=400, width=60, height=60)


def make_detection(
    frame_id: FrameId,
    bbox: BoundingBox,
    frame_position: int,
    confidence: float = 0.9,
) -> Detection:
    return Detection(
        frame_id=frame_id,
        frame_position=frame_position,
        prediction=Prediction(bbox=bbox, confidence=confidence, label=ClassLabel.PERSON),
    )


def make_adapter() -> ByteTrackTracker:
    return make_bytetrack_tracker(frame_rate=30)


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------


def test_should_return_empty_result_for_no_detections() -> None:
    assert make_adapter().track([]) == []


# ---------------------------------------------------------------------------
# Single frame
# ---------------------------------------------------------------------------


def test_single_detection_forms_one_group() -> None:
    d = make_detection(FRAME_0_ID, BBOX_A, frame_position=0)

    result = make_adapter().track([d])

    assert len(result) == 1
    assert result[0] == [d]


def test_two_distinct_detections_in_same_frame_form_two_groups() -> None:
    d_a = make_detection(FRAME_0_ID, BBOX_A, frame_position=0)
    d_b = make_detection(FRAME_0_ID, BBOX_B, frame_position=0)

    result = make_adapter().track([d_a, d_b])

    assert len(result) == 2


# ---------------------------------------------------------------------------
# Multiple frames — continuity
# ---------------------------------------------------------------------------


def test_same_object_across_two_frames_forms_one_group() -> None:
    d1 = make_detection(FRAME_0_ID, BBOX_A, frame_position=0)
    d2 = make_detection(FRAME_1_ID, BBOX_A_NEARBY, frame_position=1)

    result = make_adapter().track([d1, d2])

    assert len(result) == 1
    assert d1 in result[0]
    assert d2 in result[0]


def test_two_distinct_objects_each_tracked_across_two_frames_form_two_groups() -> None:
    # ByteTrack does not immediately confirm a new track on its first appearance
    # when other active tracks already exist. A second consecutive detection is
    # required for confirmation. Hence object B must appear on frames 1 AND 2.
    d_a0 = make_detection(FRAME_0_ID, BBOX_A, frame_position=0)
    d_a1 = make_detection(FRAME_1_ID, BBOX_A_NEARBY, frame_position=1)
    d_b1 = make_detection(FRAME_1_ID, BBOX_B, frame_position=1)
    d_b2 = make_detection(FRAME_2_ID, BoundingBox(center_x=402, center_y=402, width=60, height=60), frame_position=2)

    result = make_adapter().track([d_a0, d_a1, d_b1, d_b2])

    assert len(result) == 2
    flat = [d for group in result for d in group]
    assert d_a0 in flat
    assert d_b2 in flat


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def test_should_build_bytetrack_tracker() -> None:
    assert isinstance(make_bytetrack_tracker(), ByteTrackTracker)


def test_should_create_a_new_instance_on_every_call() -> None:
    assert make_bytetrack_tracker() is not make_bytetrack_tracker()
