# Learnings: Decouple Detection from Tracking

## Decisions Made

### Tracker returns `list[list[Detection]]`, not domain objects

- **Options considered**: return `list[Track]` (adapter creates domain objects)
  vs return `list[list[Detection]]` (workflow creates domain objects)
- **Decision**: adapter returns grouped detection sequences; workflow creates
  `Track` objects using `IdFactory`
- **Rationale**: adapters transform data, they do not aggregate domain objects
  or generate domain IDs
- **Trade-offs**: workflow takes on Track construction, but domain cohesion is
  preserved

### Grace period is an adapter implementation detail

- **Options considered**: keep `closed`/`missed_frames` on `Track` for domain
  visibility vs hide inside adapter
- **Decision**: remove from `Track`; ByteTrackTracker handles grace period
  internally
- **Rationale**: no business use case needs to know "how close a track is to
  being closed" — only the tracking algorithm cares
- **Trade-offs**: less observable state on Track; grace period behaviour tested
  at integration level (ByteTrackTracker tests), not domain level

### Detection phase publishes `FrameDetected` (not full analysis)

- **Options considered**: publish after tracking (accurate name) vs publish
  after detection (streaming progress)
- **Decision**: publish per frame at detection time; tracking is a single fast
  pass at the end
- **Rationale**: detection is the slow GPU phase; progress feedback is
  meaningful at detection time; tracking is near-instant

### No `DetectionRepository` for MVP

- **Options considered**: persist detections for re-tracking vs keep in local
  list
- **Decision**: local list in `VideoAnalysisWorkflow.execute()` — re-run full
  analysis when needed
- **Rationale**: MVP; re-detection is acceptable; avoids a new gateway +
  implementation

## Gotchas

### ByteTrack does not immediately confirm new tracks when active tracks already exist

- **Context**: writing integration tests for `ByteTrackTracker.track()`
- **Issue**: a detection that cannot match any existing active track is added as
  "unconfirmed" by ByteTrack and is NOT returned in `update()` output until a
  second consecutive detection matches it
- **Solution**: tests for "two distinct objects" need at least 2 frames of each
  object to confirm both; a single-frame object simply won't appear in the
  output if another active track already exists
- **Note**: this behaviour is consistent with the old per-frame design (orphan
  detections were also only "confirmed" after multiple frames of occurrence)
