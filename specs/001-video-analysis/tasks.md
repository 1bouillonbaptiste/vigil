---

description: "Task list for Video Analysis Report (001-video-analysis)"
---

# Tasks: Video Analysis Report

**Input**: Design documents from `/specs/001-video-analysis/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project — `vigil/` package at repository root, `tests/` alongside it.

---

## Phase 1: Setup

**Purpose**: Add new dependencies and create scaffolding for directories that don't exist yet.

- [X] T001 Add dependencies to `pyproject.toml` via Poetry: `fastapi`, `uvicorn`, `opencv-python-headless`, `ultralytics`
- [X] T002 [P] Create package directories with `__init__.py`: `vigil/business_logic/services/`, `vigil/adapters/primary/`, `vigil/adapters/primary/api/`, `vigil/adapters/primary/api/routes/`, `reports/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Breaking changes to the domain model that must land before any new code.
All existing tests will fail until T005, T006, and T011 are complete.

⚠️ **CRITICAL**: Complete this entire phase before starting any user story phase.

- [X] T003 Create `ObjectClass` str-enum (`PERSON`, `VEHICLE`) in `vigil/business_logic/models/object_class.py`
- [X] T004 [P] Create `RawFrame` frozen dataclass (`index: int`, `data: bytes`) in `vigil/business_logic/models/raw_frame.py`
- [X] T005 Add `object_class: ObjectClass` field to `Detection` in `vigil/business_logic/models/detection.py` (import from `object_class.py`; no default — breaking change)
- [X] T006 Add `object_class: ObjectClass` field to `Track`; update `Track.create()` to derive it by majority vote over `detection.object_class` for each detection in `vigil/business_logic/models/track.py`
- [X] T007 [P] Add `save(detection: Detection) -> None` method to `DetectionRepository` protocol in `vigil/business_logic/gateways/detection_repository.py`
- [X] T008 [P] Add `list_by_video_id(video_id: UUID) -> list[Track]` method to `TrackRepository` protocol in `vigil/business_logic/gateways/track_repository.py`
- [X] T009 [P] Add `save(detection: Detection) -> None` as alias of `add()` in `InMemoryDetectionRepository` in `vigil/adapters/secondary/in_memory_detection_repository.py`
- [X] T010 Fix `IouTracker._find_detections_on_frame` to find the **nearest next frame index** greater than the current one (not exactly `frame_index + 1`) in `vigil/adapters/secondary/iou_tracker.py` — required for frame-sampled input where indices step by `frame_interval`
- [X] T011 Update `DetectionFactory.create()` in `tests/helpers.py` to accept `object_class: ObjectClass = ObjectClass.PERSON`; fix all callers in `tests/unit/test_track_objects.py` and `tests/integration/` to compile and pass

**Checkpoint**: All existing tests pass again. Foundation ready for user story work.

---

## Phase 3: User Story 1 — Submit Video and Receive Analysis Report (Priority: P1) 🎯 MVP

**Goal**: `POST /analyse` accepts a video path and returns a JSON report with one entry
per tracked object (ID, class, frame range, thumbnail reference).

**Independent Test**: Run `POST /analyse` against a short test video containing a person
and a vehicle. Response is valid JSON with ≥2 track entries (one `"person"`, one
`"vehicle"`), each with `track_id`, `object_class`, `first_frame_index`,
`last_frame_index`, and `thumbnail_detection_id`.

### Ports and Domain Models for User Story 1

- [X] T012 [P] [US1] Define `DetectionModel` protocol (`detect(frame: RawFrame, video_id: UUID) -> list[Detection]`) in `vigil/business_logic/gateways/detection_model.py`
- [X] T013 [P] [US1] Define `VideoReader` protocol (`read(video_path: str, frame_interval: int) -> Iterator[RawFrame]`) and `VideoDurationExceededError` exception in `vigil/business_logic/gateways/video_reader.py`
- [X] T014 [P] [US1] Define `ReportWriter` protocol (`write(report: Report) -> None`) in `vigil/business_logic/gateways/report_writer.py`
- [X] T015 [P] [US1] Create `TrackSummary` and `Report` frozen dataclasses in `vigil/business_logic/models/report.py` — `TrackSummary` fields: `track_id`, `object_class`, `first_frame_index`, `last_frame_index`, `first_bbox`, `last_bbox`, `thumbnail_detection_id`; `Report` fields: `video_id`, `track_summaries`

### Use Case for User Story 1

- [X] T016 [US1] Implement `DetectObjectsUseCase` in `vigil/business_logic/use_cases/detect_objects.py` — constructor takes `detection_model: DetectionModel` and `detection_repository: DetectionRepository`; `execute(frame: RawFrame, video_id: UUID) -> None` calls `detection_model.detect()` then `detection_repository.save()` for each result (depends on T012)
- [X] T017 [US1] Write unit tests for `DetectObjectsUseCase` in `tests/unit/test_detect_objects.py` using a fake `DetectionModel` and `InMemoryDetectionRepository`; test: "detections from frame are saved to repository"; "empty frame produces no detections"; "detections are attributed to the correct video"

### Application Service for User Story 1

- [X] T018 [US1] Implement `AnalyseVideoService` in `vigil/business_logic/services/analyse_video.py` — constructor takes `video_reader`, `detect_objects_uc`, `track_objects_uc`, `track_repository`, `detection_repository`, `report_writer`, `frame_interval: int = 5`; `execute(video_path: str, video_id: UUID) -> Report` runs the full pipeline: iterate frames → detect per frame → track → build Report → write (depends on T013–T016)
- [X] T019 [US1] Write unit tests for `AnalyseVideoService` in `tests/unit/test_analyse_video.py` using fakes for all ports; test: "a video with two trackable objects produces a report with two track summaries"; "a video with no objects produces an empty report"; "report is passed to report writer"

### Infrastructure Adapters for User Story 1

- [X] T020 [P] [US1] Implement `Cv2VideoReader` in `vigil/adapters/secondary/cv2_video_reader.py` — reads video with `cv2.VideoCapture`, checks duration before yielding frames (`VideoDurationExceededError` if > 5 minutes), yields `RawFrame(index, jpeg_bytes)` every `frame_interval` frames
- [X] T021 [P] [US1] Implement `YoloDetectionModel` in `vigil/adapters/secondary/yolo_detection_model.py` — loads `yolov8n.pt`, decodes `RawFrame.data` from bytes, runs inference, maps COCO class IDs `{0→PERSON, 2,3,5,7→VEHICLE}` to `ObjectClass`, returns `list[Detection]`; all other class IDs are ignored
- [X] T022 [P] [US1] Implement `JsonReportWriter` in `vigil/adapters/secondary/json_report_writer.py` — writes `Report` as JSON to `{reports_dir}/{video_id}.json`; constructor takes `reports_dir: str = "reports"`

### API for User Story 1

- [X] T023 [US1] Create FastAPI app factory `create_app() -> FastAPI` in `vigil/adapters/primary/api/app.py` — wires all concrete adapters (`Cv2VideoReader`, `YoloDetectionModel`, `InMemoryDetectionRepository`, `InMemoryTrackRepository`, `IouTracker`, `JsonReportWriter`) into `AnalyseVideoService` and registers routes
- [X] T024 [US1] Implement `POST /analyse` route in `vigil/adapters/primary/api/routes/analyse.py` — request body `{"video_path": str}`, calls service, returns `Report` as JSON; handles `VideoDurationExceededError` → 422, `FileNotFoundError` → 400 (depends on T023)

### Integration Tests for User Story 1

- [X] T025 [P] [US1] Write integration test for `Cv2VideoReader` in `tests/integration/test_cv2_video_reader.py` — label with `@pytest.mark.integration`; requires a short fixture video in `tests/fixtures/`; verify: frames are yielded, `frame_interval` skips correctly, duration check raises on long video
- [X] T026 [P] [US1] Write integration test for `YoloDetectionModel` in `tests/integration/test_yolo_detection_model.py` — label with `@pytest.mark.integration`; supply a `RawFrame` from a known image; verify at least one detection is returned with a valid `ObjectClass`

**Checkpoint**: `POST /analyse` works end-to-end on a test video. User Story 1 independently testable.

---

## Phase 4: User Story 2 — Track Entries Include Spatial Context (Priority: P2)

**Goal**: Each track entry in the report includes `first_bbox` and `last_bbox` — the
bounding-box position at the object's first and last appearance.

**Independent Test**: Submit a test video where a person walks across the frame.
Verify `first_bbox.center_x` and `last_bbox.center_x` differ, confirming movement
was captured. Test independently of US3.

- [X] T027 [US2] Enrich `AnalyseVideoService._build_report()` (or equivalent internal method) in `vigil/business_logic/services/analyse_video.py` to look up the first and last `Detection` for each track from `DetectionRepository`, and populate `TrackSummary.first_bbox` and `TrackSummary.last_bbox`
- [X] T028 [US2] Add unit test case to `tests/unit/test_analyse_video.py`: "track summary includes first and last bounding box from the track's detections" — verify `first_bbox` equals the bbox of the detection with the lowest `frame_index`, `last_bbox` equals the bbox of the detection with the highest `frame_index`

**Checkpoint**: Report entries include spatial data. User Stories 1 and 2 pass independently.

---

## Phase 5: User Story 3 — Retrieve Previously Completed Analysis (Priority: P3)

**Goal**: `GET /reports/{video_id}` returns the stored report without re-running analysis.

**Independent Test**: Call `POST /analyse`, record `video_id`, then call
`GET /reports/{video_id}` and verify the response is identical. Confirm in server
logs that no YOLO inference ran on the second call.

- [X] T029 [US3] Define `ReportReader` protocol (`read(video_id: UUID) -> Report | None`) in `vigil/business_logic/gateways/report_reader.py`
- [X] T030 [US3] Implement `JsonReportReader` in `vigil/adapters/secondary/json_report_writer.py` (same file as writer) — reads `{reports_dir}/{video_id}.json`, deserialises to `Report`; returns `None` if file absent (depends on T029)
- [X] T031 [US3] Implement `GET /reports/{video_id}` route in `vigil/adapters/primary/api/routes/analyse.py` — calls `report_reader.read(video_id)`; returns report JSON or 404 (depends on T029, T030)

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, lint, and documentation.

- [X] T032 [P] Run `poetry run ruff check .` and fix any lint errors across all new and modified files
- [ ] T033 [P] Validate end-to-end by following `specs/001-video-analysis/quickstart.md` — confirm all checklist items pass
- [X] T034 [P] Ensure all new packages have `__init__.py` files; verify `vigil/business_logic/services/__init__.py` and `vigil/adapters/primary/__init__.py` exist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 completion
- **US2 (Phase 4)**: Depends on Phase 3 (T018 must exist before T027 can enhance it)
- **US3 (Phase 5)**: Depends on Phase 3 (T022 must exist before T030; T023/T024 before T031)
- **Polish (Phase 6)**: Depends on all desired user stories complete

### Within Each Phase — Parallel Opportunities

**Phase 2** (after T003):
```
T004 ──────────────────────────────────── parallel
T005 (depends T003)
T006 (depends T003, T005)
T007, T008, T009 ──────────────────────── parallel
T010 ────────────────────────────────────── independent
T011 (depends T005)
```

**Phase 3** (after Phase 2):
```
T012, T013, T014, T015 ─────────────────── parallel (ports + models)
T016 (depends T012)
T017 (depends T016)
T018 (depends T013, T014, T015, T016)
T019 (depends T018)
T020, T021, T022 ───────────────────────── parallel (adapters)
T023 (depends T018, T020, T021, T022)
T024 (depends T023)
T025 (depends T020) ────────────────────── parallel
T026 (depends T021) ────────────────────── parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational ⚠️ CRITICAL
3. Complete Phase 3: User Story 1
4. **STOP AND VALIDATE**: Run `POST /analyse` against a test video, confirm JSON report is returned
5. Deploy/demo MVP

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation
2. Phase 3 → Working `POST /analyse` → **Demo**
3. Phase 4 → Spatial context in report → **Demo**
4. Phase 5 → Report retrieval → **Demo**
5. Phase 6 → Polish

---

## Notes

- `[P]` tasks in the same phase can be launched in separate agents
- Foundational tasks (T003–T011) are the riskiest: T005, T006, T010, T011 all touch existing
  production code and tests — complete and verify them before any US work
- Integration tests (T025, T026) require a small test fixture video in `tests/fixtures/`;
  create a synthetic 3-second MP4 if a real video is unavailable
- YOLO model weights (`yolov8n.pt`) are downloaded automatically on first use by `ultralytics`
- `InMemoryDetectionRepository` and `InMemoryTrackRepository` are used in the app wiring
  (T023) for v1 — reports/ dir on disk is the only persistence
