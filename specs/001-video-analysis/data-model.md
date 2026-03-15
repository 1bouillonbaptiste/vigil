# Data Model: Video Analysis Report (001-video-analysis)

**Phase**: 1 — Design
**Date**: 2026-03-15

---

## Overview

The model adds two new domain entities (`Report`, `ObjectClass`), one application
value object (`RawFrame`), modifies two existing domain entities (`Detection`,
`Track`), and introduces four new ports.

---

## Domain Value Objects

### ObjectClass *(new)*

```text
Location: vigil/business_logic/models/object_class.py

Fields:
  PERSON  = "person"
  VEHICLE = "vehicle"

Type: str enum (Python Enum subclassing str for JSON serialisability)
```

Rules:
- Only `PERSON` and `VEHICLE` are valid for v1.
- YOLO class IDs are mapped to this enum exclusively inside the YOLO adapter.

---

### BoundingBox *(existing, no change)*

```text
Location: vigil/business_logic/models/detection.py

Fields:
  center_x: int   — pixels from bottom-left
  center_y: int   — pixels from bottom-left
  width:    int   — pixels
  height:   int   — pixels
```

---

### RawFrame *(new — application-layer value object)*

```text
Location: vigil/business_logic/models/raw_frame.py

Fields:
  index: int    — actual frame index in the source video (e.g. 0, 5, 10 …)
  data:  bytes  — JPEG-encoded image
```

Rules:
- `data` MUST be a valid JPEG byte sequence.
- `index` MUST be the actual video frame number, not a sequential sample counter.
- This type lives in the application layer to keep numpy out of ports and use
  cases (Constitution II).

---

## Domain Entities

### Detection *(existing — breaking change)*

```text
Location: vigil/business_logic/models/detection.py

Fields:
  id:           UUID
  video_id:     UUID
  frame_index:  int          — actual source frame index
  bbox:         BoundingBox
  confidence:   float        — 0.0–1.0
  object_class: ObjectClass  ← NEW FIELD
```

Rules:
- `object_class` MUST be set at construction; no default.
- `score()` = `confidence × bbox.area` (unchanged).
- **Breaking**: all existing `Detection` construction sites and `DetectionFactory`
  must be updated to supply `object_class`.

---

### Track *(existing — breaking change)*

```text
Location: vigil/business_logic/models/track.py

Fields:
  id:           UUID
  video_id:     UUID
  detections:   list[UUID]   — ordered detection IDs
  thumbnail_id: UUID
  object_class: ObjectClass  ← NEW FIELD
```

Rules:
- `object_class` is derived at `Track.create()` time by majority vote over the
  constituent detections' classes.
- `is_valid()` requires `len(detections) > 4` (unchanged).
- `thumbnail_id` is the detection with the highest `score()` (unchanged).

---

### Report *(new)*

```text
Location: vigil/business_logic/models/report.py

Fields:
  video_id:       UUID
  track_summaries: list[TrackSummary]
```

#### TrackSummary *(new, nested value object)*

```text
Fields:
  track_id:              UUID
  object_class:          ObjectClass
  first_frame_index:     int
  last_frame_index:      int
  first_bbox:            BoundingBox
  last_bbox:             BoundingBox
  thumbnail_detection_id: UUID
```

Rules:
- `first_frame_index` ≤ `last_frame_index`.
- `Report` is constructed by `AnalyseVideoService` after tracking completes.
- `Report` is serialised to JSON by the `JsonReportWriter` adapter.

---

## Application Ports (Interfaces)

### DetectionModel *(new)*

```text
Location: vigil/business_logic/gateways/detection_model.py

Methods:
  detect(frame: RawFrame, video_id: UUID) -> list[Detection]
```

Rules:
- Returns an empty list if no supported objects are found in the frame.
- MUST map infrastructure class IDs to `ObjectClass` internally; never expose
  raw class names or integer IDs to callers.

---

### VideoReader *(new)*

```text
Location: vigil/business_logic/gateways/video_reader.py

Methods:
  read(video_path: str, frame_interval: int) -> Iterator[RawFrame]
```

Rules:
- MUST raise `VideoDurationExceededError` (application-layer exception) before
  yielding any frames if the video exceeds 5 minutes.
- `frame_interval=1` yields every frame; `frame_interval=5` yields every 5th.
- `RawFrame.index` MUST be the actual source frame number.

---

### ReportWriter *(new)*

```text
Location: vigil/business_logic/gateways/report_writer.py

Methods:
  write(report: Report) -> None
```

Rules:
- MUST be idempotent: writing a report for the same `video_id` twice overwrites
  the previous one.

---

### ReportReader *(new)*

```text
Location: vigil/business_logic/gateways/report_reader.py

Methods:
  read(video_id: UUID) -> Report | None
```

Rules:
- Returns `None` if no report exists for the given `video_id`.

---

### DetectionRepository *(existing — protocol change)*

```text
Location: vigil/business_logic/gateways/detection_repository.py

Methods (add):
  save(detection: Detection) -> None   ← NEW (was add() on implementation only)
```

---

### TrackRepository *(existing — protocol change)*

```text
Location: vigil/business_logic/gateways/track_repository.py

Methods (add):
  list_by_video_id(video_id: UUID) -> list[Track]   ← NEW (was only on impl)
```

---

## Application Service

### AnalyseVideoService *(new)*

```text
Location: vigil/business_logic/services/analyse_video.py

Constructor dependencies:
  video_reader:          VideoReader
  detect_objects_uc:     DetectObjectsUseCase
  track_objects_uc:      TrackObjectsUseCase
  track_repository:      TrackRepository
  detection_repository:  DetectionRepository
  report_writer:         ReportWriter
  frame_interval:        int = 5

Method:
  execute(video_path: str, video_id: UUID) -> Report
```

Execution order:
1. Iterate frames via `video_reader.read(video_path, frame_interval)`.
2. For each `RawFrame`, call `detect_objects_uc.execute(frame, video_id)`.
3. After all frames: call `track_objects_uc.execute(video_id)`.
4. Fetch tracks: `track_repository.list_by_video_id(video_id)`.
5. Fetch detections: `detection_repository.get_by_video_id(video_id)`.
6. Build `Report` domain entity from tracks + detections.
7. `report_writer.write(report)`.
8. Return `Report`.

---

## Infrastructure Adapters (New)

| Adapter | Port Implemented | Location |
|---------|-----------------|----------|
| `Cv2VideoReader` | `VideoReader` | `vigil/adapters/secondary/cv2_video_reader.py` |
| `YoloDetectionModel` | `DetectionModel` | `vigil/adapters/secondary/yolo_detection_model.py` |
| `JsonReportWriter` | `ReportWriter` | `vigil/adapters/secondary/json_report_writer.py` |
| `JsonReportReader` | `ReportReader` | `vigil/adapters/secondary/json_report_writer.py` (same file) |

---

## Entity Relationship Summary

```text
Video (path, id)
  │ 1
  │ produces
  │ N
RawFrame (index, data:bytes)
  │ 1
  │ yields detections via DetectionModel
  │ N
Detection (id, video_id, frame_index, bbox, confidence, object_class)
  │ N
  │ grouped by IouTracker into
  │ 1
Track (id, video_id, detections:list[UUID], thumbnail_id, object_class)
  │ N
  │ summarised into
  │ 1
Report (video_id, track_summaries:list[TrackSummary])
```
