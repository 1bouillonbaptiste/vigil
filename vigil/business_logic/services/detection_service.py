from vigil.business_logic.gateways.detection_model import DetectionModel
from vigil.business_logic.models.detection import Detection
from vigil.business_logic.models.frame import Frame


class DetectionService:
    """Run object detection on a batch of frames.

    Deep-learning models process a batch of images in a single forward pass,
    which is an order of magnitude faster than running one image at a time.
    This service exposes that batch interface directly: the caller decides the
    batch size based on the operational context — large batches for post-analysis
    on a full video, a batch of one for real-time processing.

    No IO: takes frames, returns detections.
    """

    def __init__(self, model: DetectionModel) -> None:
        self._model = model

    def detect(self, frames: list[Frame]) -> list[Detection]:
        """Run detection on a batch of frames."""
        batch = [frame.data for frame in frames]
        batch_results = self._model.detect(batch)

        detections: list[Detection] = []
        for frame, bboxes in zip(frames, batch_results, strict=True):
            for bbox in bboxes:
                detections.append(
                    Detection(
                        video_id=frame.video_id,
                        frame_id=frame.id,
                        bbox=bbox,
                    )
                )
        return detections
