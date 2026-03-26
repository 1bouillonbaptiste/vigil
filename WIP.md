# WIP: Decouple Detection from Tracking

## Current Step

Step 5 of 5: Simplify `Track` + remove `list_open_tracks`

## Status

🔴 RED — writing failing tests

## Completed

- [x] Step 1: Rename `FrameAnalyzed` → `FrameDetected`
- [x] Step 2: New `Tracker.track()` Protocol + `ByteTrackTracker` +
  `FakeTracker`
- [x] Step 3: Rewrite `VideoAnalysisWorkflow`
- [x] Step 4: Delete `TrackObjectsUseCase`
- [ ] Step 2: New `Tracker.track()` + `ByteTrackTracker` + `FakeTracker`
- [ ] Step 3: Rewrite `VideoAnalysisWorkflow`
- [ ] Step 4: Delete `TrackObjectsUseCase`
- [ ] Step 5: Simplify `Track` + remove `list_open_tracks`

## Blockers

None

## Next Action

Rename `frame_analyzed.py` → `frame_detected.py`, update class name, subscriber,
workflow, main.py, and all tests
