from uuid import UUID, uuid4

import cv2
import numpy as np
from ultralytics import YOLO

from vigil.business_logic.models.detection import BoundingBox, Detection
from vigil.business_logic.models.object_class import ObjectClass
from vigil.business_logic.models.raw_frame import RawFrame

# COCO class IDs that map to supported ObjectClass values.
_COCO_TO_OBJECT_CLASS: dict[int, ObjectClass] = {
    0: ObjectClass.PERSON,  # person
    2: ObjectClass.VEHICLE,  # car
    3: ObjectClass.VEHICLE,  # motorcycle
    5: ObjectClass.VEHICLE,  # bus
    7: ObjectClass.VEHICLE,  # truck
}


class YoloDetectionModel:
    """Object detector backed by a YOLOv8 model via the ultralytics library.

    Infrastructure detail: COCO class IDs and numpy arrays never leave this adapter.
    """

    def __init__(self, model_name: str = "yolov8n.pt") -> None:
        self._model = YOLO(model_name)

    def detect(self, frame: RawFrame, video_id: UUID) -> list[Detection]:
        """Run YOLOv8 inference on a JPEG-encoded frame."""
        np_array = np.frombuffer(frame.data, dtype=np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        results = self._model(image, verbose=False)
        detections: list[Detection] = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                object_class = _COCO_TO_OBJECT_CLASS.get(class_id)
                if object_class is None:
                    continue
                x_center, y_center, width, height = box.xywh[0].tolist()
                detections.append(
                    Detection(
                        id=uuid4(),
                        video_id=video_id,
                        frame_index=frame.index,
                        bbox=BoundingBox(
                            center_x=int(x_center),
                            center_y=int(y_center),
                            width=int(width),
                            height=int(height),
                        ),
                        confidence=float(box.conf[0]),
                        object_class=object_class,
                    )
                )
        return detections
