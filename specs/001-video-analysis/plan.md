# Implementation Plan: Video Analysis Report

**Branch**: `001-video-analysis` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-video-analysis/spec.md`

## Summary

Implement the full Vigil v1 pipeline: accept a video file path via a FastAPI
endpoint, extract sampled frames with OpenCV, run YOLOv8 object detection per
frame, group detections into tracks with the existing IOU tracker, build a
structured JSON report per video, and persist it to disk. A second endpoint
retrieves previously computed reports. Three new use cases/services are added on
top of the existing `TrackObjectsUseCase`; the domain models `Detection` and
`Track` gain an `object_class` field.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI, uvicorn, opencv-python-headless, ultralytics (YOLOv8n)
**Storage**: JSON files on disk (`reports/{video_id}.json`); no database
**Testing**: pytest; unit tests with hand-written fakes; integration tests labelled
**Target Platform**: Linux server (single-process, local filesystem)
**Project Type**: web-service
**Performance Goals**: ≤3× realtime (≤3 min for a 1-min video); default 1-in-5 frame sampling
**Constraints**: 5-minute maximum video duration; no auth; no real-time processing
**Scale/Scope**: Single operator, v1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Pre-Phase-0 | Post-Phase-1 | Notes |
|-----------|-------------|--------------|-------|
| I. Clean Architecture — four layers, inward deps only | ✅ | ✅ | API → Service → UseCases → Domain; no upward refs |
| II. No Infrastructure Leakage — no numpy/SQLAlchemy in domain | ✅ | ✅ | `RawFrame.data` is `bytes`; numpy stays in YOLO adapter |
| III. Test Discipline — fakes, not mocks; sentence-named tests | ✅ | ✅ | All new use cases/services get fake-backed unit tests |
| IV. Interfaces First — ports before adapters | ✅ | ✅ | `DetectionModel`, `VideoReader`, `ReportWriter`, `ReportReader` ports defined before adapters |
| V. Scope Discipline — post-hoc video analysis only | ✅ | ✅ | Feature IS the core value proposition; no RT, no facial recognition, no NLP |
| Language/Stack — Python 3.13+, Poetry, ruff | ✅ | ✅ | Confirmed in Technical Context |

**Result**: All gates pass. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-video-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api.md           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
vigil/
├── business_logic/
│   ├── models/
│   │   ├── detection.py          ← MODIFY: add object_class field (breaking)
│   │   ├── track.py              ← MODIFY: add object_class field (breaking)
│   │   ├── object_class.py       ← NEW: ObjectClass enum (PERSON, VEHICLE)
│   │   ├── raw_frame.py          ← NEW: RawFrame(index, data:bytes)
│   │   └── report.py             ← NEW: Report + TrackSummary
│   ├── gateways/
│   │   ├── detection_repository.py  ← MODIFY: add save() to protocol
│   │   ├── track_repository.py      ← MODIFY: add list_by_video_id() to protocol
│   │   ├── detection_model.py       ← NEW: DetectionModel port
│   │   ├── video_reader.py          ← NEW: VideoReader port
│   │   ├── report_writer.py         ← NEW: ReportWriter port
│   │   ├── report_reader.py         ← NEW: ReportReader port
│   │   ├── tracker.py               (existing — no change)
│   ├── use_cases/
│   │   ├── track_objects.py         (existing — no change)
│   │   └── detect_objects.py        ← NEW: DetectObjectsUseCase
│   └── services/
│       └── analyse_video.py         ← NEW: AnalyseVideoService
├── adapters/
│   ├── primary/
│   │   └── api/
│   │       ├── app.py               ← NEW: FastAPI app factory
│   │       └── routes/
│   │           └── analyse.py       ← NEW: POST /analyse + GET /reports/{video_id}
│   └── secondary/
│       ├── cv2_video_reader.py       ← NEW: OpenCV VideoReader adapter
│       ├── yolo_detection_model.py   ← NEW: YOLOv8 DetectionModel adapter
│       ├── json_report_writer.py     ← NEW: JSON ReportWriter + ReportReader adapter
│       ├── in_memory_detection_repository.py  (existing — add save() method)
│       ├── in_memory_track_repository.py      (existing — no change needed)
│       └── iou_tracker.py            ← MODIFY: handle non-consecutive frame indices

tests/
├── unit/
│   ├── test_track_objects.py    (existing — update DetectionFactory calls)
│   ├── test_detect_objects.py   ← NEW
│   └── test_analyse_video.py    ← NEW
├── integration/
│   ├── test_in_memory_track_repository.py  (existing)
│   ├── test_iou_tracker.py                 (existing — add frame-gap test)
│   ├── test_cv2_video_reader.py            ← NEW (requires fixture video)
│   └── test_yolo_detection_model.py        ← NEW (requires fixture video)
└── helpers.py                              ← MODIFY: add object_class to DetectionFactory
```

**Structure Decision**: Single-project layout with Clean Architecture layering.
The existing `vigil/` package structure is extended; no new top-level packages.
`services/` subfolder added under `business_logic/` for the `AnalyseVideoService`
orchestrator (distinct from use cases per plan.md Task 6).

## Complexity Tracking

> No constitution violations. Section left blank.

---

## Key Design Decisions

See `research.md` for full rationale. Summary:

1. **Object classes**: `PERSON` and `VEHICLE` only. Task 3 in plan.md mentions
   "person only" — this conflicts with the spec (FR-009). **Spec wins**: both
   classes are implemented.

2. **Frame boundary type**: `RawFrame.data: bytes` (JPEG-encoded). Keeps numpy
   out of the application layer (Constitution II).

3. **Frame sampling**: `VideoReader` accepts `frame_interval`; `RawFrame.index`
   is the actual source frame number. Default `frame_interval=5` (configurable).

4. **IOU tracker fix**: `IouTracker` must search for the nearest next-frame
   detection rather than exactly `frame_index + 1`. With 1-in-5 sampling,
   consecutive sampled frames differ by 5 in index; the current `+1` logic
   breaks tracking entirely.

5. **Duration validation**: `VideoReader` adapter raises `VideoDurationExceededError`
   (application-layer exception) before decoding if video > 5 minutes.

6. **Report storage**: `reports/{video_id}.json` at repo root. Deterministic
   filename; write is idempotent.

7. **AnalyseVideoService** is an application service (not a use case). It
   orchestrates `DetectObjectsUseCase` per frame, then `TrackObjectsUseCase`,
   then builds and writes the `Report`.

---

## Breaking Changes

These existing files must be updated before new code can be added:

| File | Change |
|------|--------|
| `vigil/business_logic/models/detection.py` | Add `object_class: ObjectClass` field to `Detection` |
| `vigil/business_logic/models/track.py` | Add `object_class: ObjectClass` field to `Track`; update `Track.create()` |
| `vigil/business_logic/gateways/detection_repository.py` | Add `save(detection)` to protocol |
| `vigil/business_logic/gateways/track_repository.py` | Add `list_by_video_id(video_id)` to protocol |
| `vigil/adapters/secondary/in_memory_detection_repository.py` | Rename/alias `add` → `save` in protocol |
| `vigil/adapters/secondary/iou_tracker.py` | Fix next-frame matching for non-consecutive indices |
| `tests/helpers.py` | Add `object_class` param to `DetectionFactory.create()` |
| All existing tests using `Detection` directly | Pass `object_class` |
