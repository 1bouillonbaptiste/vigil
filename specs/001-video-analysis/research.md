# Research: Video Analysis Report (001-video-analysis)

**Phase**: 0 — Outline & Research
**Date**: 2026-03-15

---

## Decision 1: Object Classes Supported

**Decision**: Two classes — `PERSON` and `VEHICLE` (unified, no subtypes for v1).

**Rationale**: Spec FR-009 specifies `person` and `vehicle` as the two supported
classes. Note: `plan.md` Task 3 says "The domain supports only person classes,
filter vehicles and other classes" — this is inconsistent with the spec and was
likely an early draft. The spec takes precedence; both person and vehicle are in
scope.

**Alternatives considered**:
- Vehicle subtypes (car, truck, motorcycle, bicycle): deferred to a future version
  per user decision.
- Person only: inconsistent with the spec and product description.

---

## Decision 2: Image Representation Across the Domain Boundary

**Decision**: Raw frames are represented as `bytes` (JPEG-encoded) in the
application layer. The `RawFrame` value object carries `index: int` and
`data: bytes`.

**Rationale**: `numpy.ndarray` is an infrastructure type (from OpenCV/YOLO) and
MUST NOT appear in the domain or application layers (Constitution II). JPEG
encoding is a well-supported, lossless-enough intermediate format for this use
case. Both the OpenCV adapter (encoding) and the YOLO adapter (decoding) handle
the conversion internally.

**Alternatives considered**:
- Pass `numpy.ndarray` directly: violates Constitution II — no infrastructure
  types in application layer.
- Opaque `ImageToken` with a UUID: adds indirection without benefit; JPEG bytes
  is explicit and portable.
- Combine VideoReader + ObjectDetector into a single port: coarser boundary,
  harder to fake in unit tests.

---

## Decision 3: Frame Sampling Strategy

**Decision**: The `VideoReader` port exposes a `frame_interval` parameter.
When `frame_interval=5` (the v1 default), it reads every 5th frame. The
`frame_index` stored in `Detection` is the **actual source frame index** in the
video (e.g., 0, 5, 10, 15…), not a sequential sample counter.

**Rationale**: Preserving actual frame indices keeps the report spatially and
temporally accurate (operators can seek to the exact frame). The sampling is a
VideoReader-level concern; downstream components are unaware of it.

**Impact on IOU Tracker**: The `IouTracker` currently matches detections at
exactly `frame_index + 1`. With frame sampling, consecutive sampled frames are
5 apart (0 → 5 → 10…), so the tracker will never find a match and will produce
only single-detection tracks (all filtered by the 5-detection minimum).
**Fix required**: `IouTracker` must be updated to search for the detection with
the smallest next `frame_index` greater than the current one (i.e., find the
nearest next frame with a detection), not exactly `frame_index + 1`.

**Alternatives considered**:
- Sequential sample counter (0, 1, 2…): loses the actual frame position,
  making report seek-back impossible.
- No frame sampling: too slow for the ≤3× realtime target.

---

## Decision 4: Video Duration Validation

**Decision**: Validation happens inside the `VideoReader` adapter at the point
of reading metadata (before any frame decoding). If a video exceeds 5 minutes,
the adapter raises a `VideoDurationExceededError` (defined in the application
layer). The API endpoint catches this and returns HTTP 422.

**Rationale**: Early rejection avoids loading any frames from oversize videos.
OpenCV's `CAP_PROP_FRAME_COUNT` and `CAP_PROP_FPS` properties expose duration
metadata cheaply without decoding frames.

**Alternatives considered**:
- Validate at the API layer: requires the API to know about video metadata,
  which is an infrastructure concern.
- No hard limit, let processing time implicitly bound: unpredictable and
  degrades operator experience.

---

## Decision 5: YOLOv8 Class Mapping

**Decision**: In the YOLO adapter, COCO class IDs are mapped to `ObjectClass`
as follows:

| COCO class ID | COCO label  | Vigil `ObjectClass` |
|---------------|-------------|---------------------|
| 0             | person      | `PERSON`            |
| 2             | car         | `VEHICLE`           |
| 3             | motorcycle  | `VEHICLE`           |
| 5             | bus         | `VEHICLE`           |
| 7             | truck       | `VEHICLE`           |

All other COCO class IDs are ignored (no detection emitted).

**Rationale**: These are the standard COCO classes most relevant to security and
site-monitoring use cases. The mapping is encapsulated entirely within the YOLO
adapter; the domain never sees COCO IDs.

**Alternatives considered**:
- Configurable mapping via a config file: over-engineering for v1; a hardcoded
  mapping in the adapter is sufficient and explicit.

---

## Decision 6: Report Persistence (No Database V1)

**Decision**: Reports are written as JSON files to a `reports/` directory at the
repository root (or a configurable base path). The filename is
`{video_id}.json`. The `ReportWriter` port writes; a corresponding
`ReportReader` port (or the same adapter) reads by video ID.

**Rationale**: Plan.md explicitly excludes any persistent storage beyond the
output JSON file. File-based persistence requires zero infrastructure setup.

**Alternatives considered**:
- SQLite: simpler querying but adds a dependency and violates the "no storage
  beyond JSON" constraint.
- In-memory only: US3 (retrieve previous analysis) would not survive process
  restart; not acceptable.

---

## Decision 7: AnalyseVideo — Application Service, Not Use Case

**Decision**: `AnalyseVideoService` lives in
`vigil/business_logic/services/analyse_video.py`. It is an application service
that orchestrates multiple use cases (`DetectObjectsUseCase`,
`TrackObjectsUseCase`) and the `ReportWriter` port. It is NOT a use case itself.

**Rationale**: Plan.md Task 6 explicitly designates it as an application service.
Use cases have one responsibility; orchestration across multiple use cases is a
service-level concern. This matches the constitution's "Small, focused use cases.
One use case = one responsibility."

**Alternatives considered**:
- Single mega-use-case doing everything: violates single-responsibility.
- Call use cases from the API adapter: the API should be a thin adapter; no
  business orchestration logic belongs there.

---

## Decision 8: Track Object Class Derivation

**Decision**: `Track.create()` derives `object_class` by majority vote across
the constituent `Detection` objects' classes. In practice all detections in a
track will share the same class (YOLO is consistent), but majority vote guards
against edge cases.

**Rationale**: The `Track` domain object must carry an `object_class` to satisfy
FR-005. Deriving it at creation time from detections keeps the entity
self-consistent.

---

## Breaking Changes to Existing Code

The following existing components require updates:

| Component | Change | Reason |
|-----------|--------|--------|
| `Detection` model | Add `object_class: ObjectClass` field | FR-005, FR-009 |
| `Track.create()` | Add `object_class` derivation, add to `Track` fields | FR-005 |
| `TrackRepository` protocol | Add `list_by_video_id` method | needed by service |
| `DetectionRepository` protocol | Add `save` (alias `add`) method | needed by use case |
| `IouTracker` adapter | Match on nearest next frame, not `frame_index + 1` | frame sampling |
| `DetectionFactory` (tests) | Add `object_class` parameter | keeps tests compiling |
| All existing tests creating `Detection` | Pass `object_class` | breaking field addition |
