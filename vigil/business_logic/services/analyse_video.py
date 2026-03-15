from uuid import UUID

from vigil.business_logic.gateways.detection_repository import DetectionRepository
from vigil.business_logic.gateways.report_writer import ReportWriter
from vigil.business_logic.gateways.track_repository import TrackRepository
from vigil.business_logic.gateways.video_reader import VideoReader
from vigil.business_logic.models.report import Report, TrackSummary
from vigil.business_logic.use_cases.detect_objects import DetectObjectsUseCase
from vigil.business_logic.use_cases.track_objects import TrackObjectsUseCase


class AnalyseVideoService:
    """Orchestrates the full video analysis pipeline.

    Execution order:
      1. Extract sampled frames via VideoReader.
      2. Detect objects per frame via DetectObjectsUseCase.
      3. Group detections into tracks via TrackObjectsUseCase.
      4. Build a Report domain entity (with spatial context per track).
      5. Persist the report via ReportWriter.
    """

    def __init__(
        self,
        video_reader: VideoReader,
        detect_objects_uc: DetectObjectsUseCase,
        track_objects_uc: TrackObjectsUseCase,
        track_repository: TrackRepository,
        detection_repository: DetectionRepository,
        report_writer: ReportWriter,
        frame_interval: int = 5,
    ) -> None:
        self._video_reader = video_reader
        self._detect_objects_uc = detect_objects_uc
        self._track_objects_uc = track_objects_uc
        self._track_repository = track_repository
        self._detection_repository = detection_repository
        self._report_writer = report_writer
        self._frame_interval = frame_interval

    def execute(self, video_path: str, video_id: UUID) -> Report:
        """Run full analysis on the video and return the structured report."""
        for frame in self._video_reader.read(video_path, self._frame_interval):
            self._detect_objects_uc.execute(frame, video_id)

        self._track_objects_uc.execute(video_id)

        report = self._build_report(video_id)
        self._report_writer.write(report)
        return report

    def _build_report(self, video_id: UUID) -> Report:
        tracks = self._track_repository.list_by_video_id(video_id)
        detections_by_id = {d.id: d for d in self._detection_repository.get_by_video_id(video_id)}

        track_summaries = []
        for track in tracks:
            track_detections = sorted(
                [detections_by_id[d_id] for d_id in track.detections],
                key=lambda d: d.frame_index,
            )
            summary = TrackSummary(
                track_id=track.id,
                object_class=track.object_class,
                first_frame_index=track_detections[0].frame_index,
                last_frame_index=track_detections[-1].frame_index,
                first_bbox=track_detections[0].bbox,
                last_bbox=track_detections[-1].bbox,
                thumbnail_detection_id=track.thumbnail_id,
            )
            track_summaries.append(summary)

        return Report(video_id=video_id, track_summaries=track_summaries)
