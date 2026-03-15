from uuid import UUID, uuid4

from vigil.adapters.secondary.in_memory_detection_repository import InMemoryDetectionRepository
from vigil.adapters.secondary.in_memory_track_repository import InMemoryTrackRepository
from vigil.adapters.secondary.iou_tracker import IouTracker
from vigil.business_logic.models.detection import BoundingBox, Detection
from vigil.business_logic.models.object_class import ObjectClass
from vigil.business_logic.models.raw_frame import RawFrame
from vigil.business_logic.models.report import Report
from vigil.business_logic.services.analyse_video import AnalyseVideoService
from vigil.business_logic.use_cases.detect_objects import DetectObjectsUseCase
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase

VIDEO_ID = UUID("9022e4bf-4ff8-4381-8dcd-b8dd588325cb")

_DEFAULT_BBOX = BoundingBox(center_x=100, center_y=50, width=10, height=30)


def _detection(frame_index: int, object_class: ObjectClass = ObjectClass.PERSON) -> Detection:
    return Detection(
        id=uuid4(),
        video_id=VIDEO_ID,
        frame_index=frame_index,
        bbox=_DEFAULT_BBOX,
        confidence=0.9,
        object_class=object_class,
    )


class FakeVideoReader:
    """Yields a fixed sequence of RawFrames regardless of the path provided."""

    def __init__(self, frames: list[RawFrame]) -> None:
        self._frames = frames

    def read(self, video_path: str, frame_interval: int):
        yield from self._frames


class FakeDetectionModel:
    """Returns detections from a pre-built mapping of frame_index → detections."""

    def __init__(self, detections_per_frame: dict[int, list[Detection]]) -> None:
        self._map = detections_per_frame

    def detect(self, frame: RawFrame, video_id: UUID) -> list[Detection]:
        return self._map.get(frame.index, [])


class FakeReportWriter:
    """Captures written reports in memory."""

    def __init__(self) -> None:
        self.written: list[Report] = []

    def write(self, report: Report) -> None:
        self.written.append(report)


def _build_service(
    frames: list[RawFrame],
    detections_per_frame: dict[int, list[Detection]],
    report_writer: FakeReportWriter,
    detection_repo: InMemoryDetectionRepository,
    track_repo: InMemoryTrackRepository,
) -> AnalyseVideoService:
    tracker = IouTracker()
    detect_uc = DetectObjectsUseCase(
        detection_model=FakeDetectionModel(detections_per_frame),
        detection_repository=detection_repo,
    )
    track_uc = TrackObjectsUseCase(
        detection_repository=detection_repo,
        tracker=tracker,
        track_repository=track_repo,
    )
    return AnalyseVideoService(
        video_reader=FakeVideoReader(frames),
        detect_objects_uc=detect_uc,
        track_objects_uc=track_uc,
        track_repository=track_repo,
        detection_repository=detection_repo,
        report_writer=report_writer,
        frame_interval=1,
    )


def test_a_video_with_two_trackable_objects_produces_a_report_with_two_track_summaries():
    detection_repo = InMemoryDetectionRepository()
    track_repo = InMemoryTrackRepository()
    report_writer = FakeReportWriter()

    person_bbox = BoundingBox(center_x=50, center_y=50, width=10, height=30)
    vehicle_bbox = BoundingBox(center_x=900, center_y=50, width=10, height=30)

    def _person(frame_index: int) -> Detection:
        return Detection(
            id=uuid4(),
            video_id=VIDEO_ID,
            frame_index=frame_index,
            bbox=person_bbox,
            confidence=0.9,
            object_class=ObjectClass.PERSON,
        )

    def _vehicle(frame_index: int) -> Detection:
        return Detection(
            id=uuid4(),
            video_id=VIDEO_ID,
            frame_index=frame_index,
            bbox=vehicle_bbox,
            confidence=0.9,
            object_class=ObjectClass.VEHICLE,
        )

    # Person on left side frames 0-4; vehicle on right side frames 0-4 (same frames)
    person_detections = [_person(i) for i in range(5)]
    vehicle_detections = [_vehicle(i) for i in range(5)]

    frames = [RawFrame(index=i, data=b"x") for i in range(5)]
    detections_by_frame = {i: [person_detections[i], vehicle_detections[i]] for i in range(5)}

    service = _build_service(frames, detections_by_frame, report_writer, detection_repo, track_repo)
    report = service.execute("/fake/video.mp4", VIDEO_ID)

    assert len(report.track_summaries) == 2
    classes = {ts.object_class for ts in report.track_summaries}
    assert classes == {ObjectClass.PERSON, ObjectClass.VEHICLE}


def test_a_video_with_no_objects_produces_an_empty_report():
    detection_repo = InMemoryDetectionRepository()
    track_repo = InMemoryTrackRepository()
    report_writer = FakeReportWriter()
    frames = [RawFrame(index=i, data=b"x") for i in range(10)]

    service = _build_service(frames, {}, report_writer, detection_repo, track_repo)
    report = service.execute("/fake/video.mp4", VIDEO_ID)

    assert report.track_summaries == []


def test_report_is_passed_to_report_writer():
    detection_repo = InMemoryDetectionRepository()
    track_repo = InMemoryTrackRepository()
    report_writer = FakeReportWriter()
    frames = [RawFrame(index=i, data=b"x") for i in range(5)]

    service = _build_service(frames, {}, report_writer, detection_repo, track_repo)
    report = service.execute("/fake/video.mp4", VIDEO_ID)

    assert len(report_writer.written) == 1
    assert report_writer.written[0] is report


def test_track_summary_includes_first_and_last_bounding_box_from_the_tracks_detections():
    detection_repo = InMemoryDetectionRepository()
    track_repo = InMemoryTrackRepository()
    report_writer = FakeReportWriter()

    # Use large overlapping boxes so the IouTracker links them into one track.
    # Boxes shift slightly left→right; each consecutive pair overlaps significantly.
    first_bbox = BoundingBox(center_x=100, center_y=100, width=100, height=100)
    mid_bbox = BoundingBox(center_x=130, center_y=100, width=100, height=100)
    last_bbox = BoundingBox(center_x=160, center_y=100, width=100, height=100)

    detections = [
        Detection(
            id=uuid4(),
            video_id=VIDEO_ID,
            frame_index=0,
            bbox=first_bbox,
            confidence=0.9,
            object_class=ObjectClass.PERSON,
        ),
        Detection(
            id=uuid4(), video_id=VIDEO_ID, frame_index=1, bbox=mid_bbox, confidence=0.9, object_class=ObjectClass.PERSON
        ),
        Detection(
            id=uuid4(), video_id=VIDEO_ID, frame_index=2, bbox=mid_bbox, confidence=0.9, object_class=ObjectClass.PERSON
        ),
        Detection(
            id=uuid4(), video_id=VIDEO_ID, frame_index=3, bbox=mid_bbox, confidence=0.9, object_class=ObjectClass.PERSON
        ),
        Detection(
            id=uuid4(),
            video_id=VIDEO_ID,
            frame_index=4,
            bbox=last_bbox,
            confidence=0.9,
            object_class=ObjectClass.PERSON,
        ),
    ]
    frames = [RawFrame(index=i, data=b"x") for i in range(5)]
    detections_by_frame = {d.frame_index: [d] for d in detections}

    service = _build_service(frames, detections_by_frame, report_writer, detection_repo, track_repo)
    report = service.execute("/fake/video.mp4", VIDEO_ID)

    assert len(report.track_summaries) == 1
    summary = report.track_summaries[0]
    assert summary.first_bbox == first_bbox
    assert summary.last_bbox == last_bbox
    assert summary.first_frame_index == 0
    assert summary.last_frame_index == 4
