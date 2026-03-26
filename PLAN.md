# Plan: Decouple Detection from Tracking

## Goal

Replace the per-frame stateful tracker with a single batch
`track(detections) -> list[list[Detection]]` call, simplify the `Track`
aggregate, delete `TrackObjectsUseCase`, and rename `FrameAnalyzed` →
`FrameDetected`.

## Acceptance Criteria

- [ ] `FrameDetected` event replaces `FrameAnalyzed` everywhere; subscriber and
  progress logic unchanged
- [ ] `Tracker` Protocol exposes `track(detections) -> list[list[Detection]]`
  only
- [ ] `VideoAnalysisWorkflow` runs detection in batches, publishes
  `FrameDetected` per frame, then calls `tracker.track()` once and persists the
  resulting Tracks
- [ ] `TrackObjectsUseCase` is deleted
- [ ] `Track` carries only `id`, `video_id`, `detections` — no `closed`,
  `missed_frames`, `extend`, `miss`
- [ ] `TrackRepository.list_open_tracks()` is deleted
- [ ] All tests pass at every step; 100% coverage maintained

## Steps

### Step 1 — Rename `FrameAnalyzed` → `FrameDetected`

**Test**: update every test that imports or references `FrameAnalyzed`; they
should pass with the new name **Implementation**: rename `frame_analyzed.py` →
`frame_detected.py`; rename the class, the subscriber, the handler method, and
all call sites in the workflow and `main.py` **Done when**: `poetry run pytest`
is green; no symbol named `FrameAnalyzed` remains

______________________________________________________________________

### Step 2 — New `Tracker.track()` Protocol + `ByteTrackTracker` + `FakeTracker`

**Test**: new integration tests for
`ByteTrackTracker.track(ordered_detections) -> list[list[Detection]]`; new unit
tests confirming `FakeTracker.track()` groups detections by bbox
**Implementation**:

- Replace `update()` with
  `track(detections: list[Detection]) -> list[list[Detection]]` in the Protocol
- Rewrite `ByteTrackTracker.track()`: iterate frames in order, feed BYTETracker
  frame by frame internally, group detections by ByteTrack integer ID, return
  groups
- Rewrite `FakeTracker.track()`: group detections by bbox (same bbox across
  frames = same object)
- Delete old `test_bytetrack_tracker.py` (tests `update()`); write new one
  (tests `track()`)

**Done when**: new integration tests pass; `FakeTracker` satisfies the Protocol
structurally

______________________________________________________________________

### Step 3 — Rewrite `VideoAnalysisWorkflow`

**Test**: rewrite `test_video_analysis_workflow.py`; tests cover: detection
batching, `FrameDetected` published per frame, tracker called once with all
detections, tracks persisted, empty video **Implementation**:

- Detection phase: batch read → detect → extend `all_detections` list → publish
  `FrameDetected` per frame
- Tracking phase: `tracker.track(all_detections)` → for each sequence create
  `Track` via `IdFactory.new_track_id(sequence[0])` → save to repository
- Remove `TrackObjectsUseCase` from the workflow constructor and from
  `app_dependencies.py`

**Done when**: workflow tests pass; `TrackObjectsUseCase` is no longer wired in
DI

______________________________________________________________________

### Step 4 — Delete `TrackObjectsUseCase`

**Test**: delete `test_track_objects.py` **Implementation**: delete
`track_objects.py`; remove its import from `app_dependencies.py`

**Done when**: `poetry run pytest` is green; no reference to
`TrackObjectsUseCase` remains

______________________________________________________________________

### Step 5 — Simplify `Track` + remove `list_open_tracks`

**Test**: update `test_get_video_tracks.py` — remove any assertion on `closed`
or `missed_frames`; update `test_bytetrack_tracker.py` if it constructs Tracks
with those fields **Implementation**:

- Remove `closed`, `_missed_frames`, `extend()`, `miss()` from `Track`
- Remove `list_open_tracks()` from `TrackRepository` Protocol and
  `InMemoryTrackRepository`
- Update the API response schema in the tracks controller if it serialises
  `closed`
- Update the Streamlit `TrackData` model if it includes `closed`

**Done when**: `poetry run pytest` is green; `Track` has three fields only
