from uuid import UUID

from vigil.adapters.secondary.bytetrack_tracker import ByteTrackTracker, make_bytetrack_tracker
from vigil.business_logic.models.detection import BoundingBox, ClassLabel, Detection, Prediction
from vigil.business_logic.models.frame import FrameId
from vigil.business_logic.models.track import Track
from vigil.business_logic.services.id_factory import IdFactory

FRAME_1_ID = FrameId(UUID("00000000-0000-0000-0000-000000000001"))
FRAME_2_ID = FrameId(UUID("00000000-0000-0000-0000-000000000002"))
VIDEO_ID = UUID("00000000-0000-0000-0000-000000000099")

# Two bboxes with ~100% IoU (same position, slight drift)
BBOX_A = BoundingBox(center_x=100, center_y=100, width=60, height=60)
BBOX_A_NEARBY = BoundingBox(center_x=102, center_y=102, width=60, height=60)

# A bbox far from BBOX_A (IoU=0)
BBOX_B = BoundingBox(center_x=400, center_y=400, width=60, height=60)


def make_detection(frame_id: FrameId, bbox: BoundingBox, confidence: float = 0.9) -> Detection:
    return Detection(
        frame_id=frame_id,
        prediction=Prediction(bbox=bbox, confidence=confidence, label=ClassLabel.PERSON),
    )


def make_track(first_detection: Detection) -> Track:
    return Track(
        id=IdFactory.new_track_id(first_detection),
        video_id=VIDEO_ID,
        detections=(first_detection,),
    )


def make_adapter() -> ByteTrackTracker:
    return make_bytetrack_tracker(frame_rate=30)


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------


def test_should_return_no_matches_when_no_detections() -> None:
    adapter = make_adapter()

    result = adapter.update(tracks=[], detections=[])

    assert result == []


# ---------------------------------------------------------------------------
# First frame — all detections are new to ByteTrack
# ---------------------------------------------------------------------------


def test_should_return_no_domain_matches_on_first_frame() -> None:
    # ByteTrack creates a new internal track but no domain Track exists yet.
    # The use case will treat the detection as an orphan and create a domain Track.
    adapter = make_adapter()
    detection = make_detection(FRAME_1_ID, BBOX_A)

    result = adapter.update(tracks=[], detections=[detection])

    assert result == []


# ---------------------------------------------------------------------------
# Subsequent frames — ByteTrack matches to an existing internal track
# ---------------------------------------------------------------------------


def test_should_match_overlapping_detection_to_domain_track() -> None:
    adapter = make_adapter()
    detection_frame1 = make_detection(FRAME_1_ID, BBOX_A)
    detection_frame2 = make_detection(FRAME_2_ID, BBOX_A_NEARBY)

    # Frame 1: ByteTrack registers a new internal track; adapter returns no matches.
    adapter.update(tracks=[], detections=[detection_frame1])

    # Simulate the domain Track the use case would have created for the orphan.
    domain_track = make_track(detection_frame1)

    # Frame 2: ByteTrack matches the nearby detection to the same internal track.
    result = adapter.update(tracks=[domain_track], detections=[detection_frame2])

    assert result == [(domain_track, detection_frame2)]


def test_should_not_match_distant_detection_to_existing_track() -> None:
    adapter = make_adapter()
    detection_frame1 = make_detection(FRAME_1_ID, BBOX_A)
    detection_frame2 = make_detection(FRAME_2_ID, BBOX_B)

    adapter.update(tracks=[], detections=[detection_frame1])

    domain_track = make_track(detection_frame1)

    # BBOX_B is far from BBOX_A — ByteTrack cannot match them.
    result = adapter.update(tracks=[domain_track], detections=[detection_frame2])

    assert result == []


# ---------------------------------------------------------------------------
# Domain track absent (closed or not yet created)
# ---------------------------------------------------------------------------


def test_should_skip_match_when_domain_track_is_absent() -> None:
    adapter = make_adapter()
    detection_frame1 = make_detection(FRAME_1_ID, BBOX_A)
    detection_frame2 = make_detection(FRAME_2_ID, BBOX_A_NEARBY)

    adapter.update(tracks=[], detections=[detection_frame1])

    # Pass no domain tracks (simulating a closed track).
    result = adapter.update(tracks=[], detections=[detection_frame2])

    assert result == []


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def test_should_build_bytetrack_tracker() -> None:
    tracker = make_bytetrack_tracker()

    assert isinstance(tracker, ByteTrackTracker)
