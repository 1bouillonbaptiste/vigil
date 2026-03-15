# Feature Specification: Video Analysis Report

**Feature Branch**: `001-video-analysis`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Vigil is a tool for operators who need to understand what happened in a recorded video without watching it manually..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit Video and Receive Analysis Report (Priority: P1)

An operator has a recorded video and wants to know what happened in it without
watching it. They submit the video to Vigil and receive a structured JSON report
listing every moving object detected — one entry per tracked object — with enough
context to understand who was present, for how long, and roughly where in the
scene.

**Why this priority**: This is the entire product value. Without this, nothing
else is useful. Every other story builds on this outcome.

**Independent Test**: Submit a short test video known to contain a person and a
vehicle. Verify the returned JSON contains at least two entries — one classified
as a person, one as a vehicle — each with a unique track ID, a class label, and
frame-range information. No other story needs to pass for this test to deliver
value.

**Acceptance Scenarios**:

1. **Given** a recorded video file, **When** the operator submits it for
   analysis, **Then** Vigil returns a JSON report containing one entry per
   tracked object, each with a unique identifier, object class, and the range
   of frames in which the object appeared.

2. **Given** a video where no moving objects appear, **When** analysis
   completes, **Then** the report is returned with an empty tracks array and
   no error.

3. **Given** a video where only stationary background elements change,
   **When** analysis completes, **Then** no tracks are present in the report
   (spurious single-frame detections are filtered out).

---

### User Story 2 - Track Entries Include Spatial Context (Priority: P2)

An operator wants to understand not just that a person appeared, but also how
they moved through the scene: where they entered, where they exited, and a
representative still from their track. This allows the operator to answer
spatial questions (e.g., "did someone approach the entrance?") without watching
the footage.

**Why this priority**: The JSON report without positional context is barely more
useful than a count. Spatial context transforms it into actionable intelligence.
This is the second most critical outcome after basic detection.

**Independent Test**: Submit a test video where a person walks across the frame
from left to right. Verify the track entry includes positional data showing
movement across the scene and a thumbnail reference pointing to a valid
detection.

**Acceptance Scenarios**:

1. **Given** a track of a moving object, **When** the report is returned,
   **Then** each track entry includes the bounding-box position at first
   appearance, last appearance, and a reference to the most visually
   representative detection (thumbnail).

2. **Given** a track where the object is partially off-screen, **When** the
   report is returned, **Then** the spatial data reflects only the visible
   portion without error.

---

### User Story 3 - Retrieve a Previously Completed Analysis (Priority: P3)

An operator submitted a video earlier and wants to re-fetch the report without
re-processing the video. They query Vigil with the video identifier and receive
the same structured report that was generated the first time.

**Why this priority**: Re-processing is wasteful and slow. Operators should be
able to archive and re-query results. This story unlocks integration with
downstream tools that may query the same video multiple times.

**Independent Test**: Submit a video, record the video ID, then query the report
using that ID in a separate request. Verify the returned report is identical to
the one from the original submission, without re-running the analysis pipeline.

**Acceptance Scenarios**:

1. **Given** a video that has already been analyzed, **When** the operator
   requests its report by video ID, **Then** the system returns the stored
   report without re-running the analysis.

2. **Given** a video ID that has never been submitted, **When** the operator
   requests its report, **Then** the system returns a clear "not found"
   response.

---

### Edge Cases

- What happens when the submitted video file is corrupt or unreadable? System
  MUST return a clear error indicating the video could not be processed.
- What happens when the video has no valid frames? Report returns with an empty
  tracks array.
- What happens when a track appears across only one or two frames? It MUST be
  filtered from the report (too short to be meaningful; consistent with the
  5-detection minimum already established in the domain).
- What happens when a video longer than 5 minutes is submitted? System MUST
  reject it at submission time with a clear error indicating the duration limit
  (5 minutes maximum for v1).
- What happens when two objects of the same class are in the scene
  simultaneously? Each MUST appear as a separate track entry with a distinct
  identifier.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a recorded video as input and produce a
  structured JSON analysis report as output.
- **FR-002**: System MUST detect moving objects of a supported class (person,
  vehicle) across a representative sample of frames in the video.
- **FR-003**: System MUST group detections of the same physical object across
  frames into a single track, regardless of brief occlusions.
- **FR-004**: System MUST exclude tracks with fewer than 5 detections from the
  report (noise filter).
- **FR-005**: Each track entry in the report MUST include: a unique track
  identifier, the object class, the first and last frame index where the object
  appeared, and a reference to the most representative detection (thumbnail).
- **FR-006**: Each track entry MUST include the bounding-box position at first
  and last appearance to convey spatial context.
- **FR-007**: System MUST persist analysis results so they can be retrieved
  later by video identifier without re-processing.
- **FR-008**: System MUST return a clear error when a submitted video cannot
  be decoded or is otherwise invalid.
- **FR-009**: System MUST support exactly two object classes: `person` and
  `vehicle`. Vehicle subtype classification (car, truck, motorcycle, bicycle)
  is explicitly out of scope for v1.
- **FR-011**: System MUST process frames at a fixed sampling interval —
  defaulting to 1 frame out of every 5 — to keep analysis duration within the
  target range. The sampling rate MUST be configurable without a code change.
- **FR-010**: System MUST NOT perform facial recognition, real-time processing,
  natural language querying, or alerting — these are explicitly out of scope.

### Key Entities

- **Video**: A recorded video file submitted for analysis. Identified by a
  unique ID. Carries metadata (duration in frames, frame rate if available).
- **Detection**: A single observation of an object in one frame. Carries:
  video ID, frame index, bounding box (position + size), confidence score,
  and object class.
- **Track**: A sequence of detections attributed to the same physical object
  across multiple frames. Carries: video ID, ordered detection references,
  thumbnail reference (most representative detection), and derived duration
  (first to last frame index).
- **Analysis Report**: The structured output for a video. Contains the video ID,
  processing timestamp, and the list of track entries in JSON format.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can submit a video and receive a complete analysis
  report without any manual intervention.
- **SC-002**: Every moving person or vehicle appearing for more than a brief
  moment is represented by exactly one track entry in the report.
- **SC-003**: A previously analyzed video can be re-queried and returns the
  same report without triggering re-processing.
- **SC-004**: The report for a 1-minute video is returned within 3 minutes of
  submission (1–3× the video duration). Vigil is post-hoc; real-time
  throughput is not required.
- **SC-005**: The system correctly filters out spurious detections — an object
  visible in only 1–4 frames MUST NOT appear in the final report.
- **SC-006**: The report is valid JSON and can be consumed by a downstream
  tool without post-processing.

## Assumptions

- Object detection is performed offline (post-hoc), not in a streaming fashion.
- Video processing is assumed to be asynchronous; the operator waits for
  completion (no real-time constraint).
- Maximum supported video duration is 5 minutes for v1; longer videos are
  rejected at submission.
- The minimum meaningful track length (5 detections) is established domain
  knowledge and is not configurable in this scope. With a default 1-in-5 frame
  sampling rate, 5 detections correspond to approximately 25 source frames.
- Frame rate information may not always be available; temporal duration in the
  report is expressed in frame counts as the primary unit.
- There is no user authentication or access control in scope for this feature.
