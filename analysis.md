# Vigil — Architecture Design Smell Analysis

All observations are grounded in the code. File:line references are included for
every claim.

______________________________________________________________________

## Smell 1 — `ByteTrackTracker` imposes a hidden behavioral contract on its caller

**Files:** `adapters/secondary/bytetrack_tracker.py:53-68`,
`business_logic/use_cases/track_objects.py:22-31`

The adapter carries this comment:

> "Assumption: the caller creates a new domain Track for every Detection that
> this adapter returns as an orphan."

This assumption is not expressed in the `Tracker` Protocol. The Protocol
contract is:

```
update(tracks, detections) -> list[tuple[Track, Detection]]
```

Orphan detections and missed tracks are *derived* by `TrackObjectsUseCase` via
set subtraction. But `ByteTrackTracker` relies on the caller materializing
orphans into domain Tracks and persisting them — so they appear in the `tracks`
argument on the next call. If the caller doesn't do this, `_track_origin`
accumulates stale entries and ByteTrack re-assigns a new integer ID to the same
object on every subsequent frame, silently breaking continuity.

**The Protocol interface is incomplete.** The contract is partially documented
in the adapter's docstring but invisible to the Protocol consumer.

**Proposed simplification — richer return type:**

```python
@dataclass(frozen=True)
class TrackerUpdate:
    matched: list[tuple[Track, Detection]]
    orphans: list[Detection]   # caller must spawn new Tracks
    missed: list[Track]        # caller must call track.miss()
```

This moves orphan/missed computation *inside* each adapter.
`TrackObjectsUseCase` becomes a thin save loop with no set arithmetic. The
Protocol becomes self-documenting.

> **Your response:**

I originally used a tracker update DTO, but I thought it was not the job of the
secondary adapter to filter orphans and missed tracks. If I switch the tracker,
I don't want to lose or copy the matching logic. I agree the contract is a bit
odd, I haven't converged on a format for the infor transmission between the
tracker and the use case. Maybe we need a design session for this specific
thing.

______________________________________________________________________

## Smell 2 — `Tracker` Protocol is stateful but looks stateless

**Files:** `business_logic/gateways/tracker.py:7-22`,
`adapters/primary/fastapi/app_dependencies.py:35-42`

`update(tracks, detections) -> matches` looks like a pure function. It is not.
`ByteTrackTracker` maintains Kalman filter state across calls — call order
matters, and reusing a tracker across videos produces wrong results. The only
guard is the comment in `_get_tracker()`. Nothing in the domain enforces the
lifecycle.

Additionally, `_get_tracker()` creates a fresh tracker per *HTTP request*, but
`VideoAnalysisWorkflow` runs as a FastAPI background task that outlives the
request. The tracker reference is captured in the closure of the background
task, so in practice isolation holds — but the lifecycle boundary is implicit
and easy to break.

**Open question:** Are concurrent video analyses a goal? If yes, the implicit
per-request lifecycle may need hardening. A scoped factory pattern could make
this explicit:

```python
class TrackerFactory(Protocol):
    def for_video(self, video_id: UUID) -> Tracker: ...
```

> **Your response:**

Even if concurrent tracking is not really happening (tracking is fast compared
to detection), some trackers keep a motion state given a video. This state in an
internal detail of the implementations, some tracker don't carry such state
(simple iou tracking is a pure function). Your tracker factory is sound, it
explicits the creation of a new tracker per call. Maybe heavy artillery for a
new tracker instantiation ? Maybe we simply need to point it in the doc.

______________________________________________________________________

## Smell 3 — `AnalysisProgressionProjection` violates Interface Segregation

**Files:** `business_logic/gateways/analysis_progression_projection.py`,
`adapters/primary/events_subscriber/frame_analyzed_subscriber.py`,
`use_cases/get_analysis_status.py`

The Protocol exposes both `increment()` (write, used by the event subscriber)
and `count()` (read, used by the status use case). These two consumers have
non-overlapping needs.

The subscriber depends on the full Protocol but only calls `increment()`. The
status use case depends on the full Protocol but only calls `count()`.

This is a textbook ISP violation. The codebase acknowledges it ("CQRS-ish but
breaks purity").

**Proposed simplification — split the Protocol:**

```python
class AnalysisProgressionWriter(Protocol):
    def increment(self, video_id: UUID) -> None: ...

class AnalysisProgressionReader(Protocol):
    def count(self, video_id: UUID) -> int: ...
```

The in-memory implementation satisfies both. Each consumer declares only what it
uses. No behavioral change required.

> **Your response:**

Deliberate choice, the progression is used only in this context. But I agree if
the two interfaces are defined in the same file it explicits the boundary
without make the domain heavier. We may go for your proposition.

______________________________________________________________________

## Smell 4 — `Frame` carries a numpy array in the domain model

**File:** `business_logic/models/frame.py:5-6, 25`

```python
import numpy as np
import numpy.typing as npt
data: npt.NDArray[np.uint8]
```

Numpy is an infrastructure library. Its presence in the domain couples the
domain model to a specific numeric computing library. `Frame` is passed to
`DetectionService`, which passes `frame.data` to the `DetectionModel` gateway —
an adapter concern. Yet the domain carries the raw pixel buffer.

The practical cost: any test constructing a `Frame` must depend on numpy. The
conceptual cost: the domain is aware of its own internal storage format.

**Open question:** Is `Frame` intended to be a domain entity, or is it a
pipeline DTO that happens to live in the domain layer? Frames are never stored,
never have domain behavior beyond carrying pixel data to `DetectionService`. If
frames exist only to carry data through the pipeline, they may belong in the
application layer rather than the domain model — and the numpy dependency would
naturally stay out of the domain.

> **Your response:**

Numpy is a very stable dependency, it's an infrastructure detail to manage
images or arrays but the standard in the deep-learning industry. Since we're
developing a project based on AI concepts, numpy is well known, stable
dependency. I wonder if we want to be independent of numpy it will create
additional complexity. I don't know if it's worth the effort.

______________________________________________________________________

## Smell 5 — `batch_size=8` hardcoded in the DI layer

**File:** `adapters/primary/fastapi/app_dependencies.py:97`

```python
return VideoAnalysisWorkflow(..., batch_size=8)
```

`batch_size` is a technical performance parameter (GPU batch throughput). It has
no business meaning. It is hardcoded inside a DI function, invisible to
operators and absent from `Config` (`adapters/primary/fastapi/config.py`), which
currently holds only `detection_model`.

**Proposed fix:** add `batch_size: int = 8` to `Config`. All tunable parameters
become visible and overridable in one place, consistent with `detection_model`.

> **Your response:**

My goal is to somehow determine it at runtime. We could have a service dedicated
to find the optimal batch size for the hardware available. I didn't take the
time though. I think we don't have to let the user set a batch size, it needs to
be optimized at runtime automatically.

______________________________________________________________________

## Smell 6 — `_missed_frames` underscored in a public frozen dataclass

**File:** `business_logic/models/track.py:30`

```python
_missed_frames: int = field(default=0)
```

The underscore signals "private," but frozen dataclasses have no information
hiding. `_missed_frames` is part of the equality contract, it participates in
hashing, and it is accessible as `track._missed_frames`. The underscore creates
false expectations of privacy.

The field also leaks an implementation detail of the grace-period algorithm into
the aggregate's observable state. Whether that state should be observable is a
domain question: knowing how close a track is to being closed (e.g., for
alerting) could be legitimate business logic.

**Proposed simplification:** rename to `missed_frames` (remove the underscore).
The `miss()` method remains the only mutation path regardless.

> **Your response:**

The intent was to let the Frame entity manage its own internal state. I don't
want to store in a repository this state (maybe we should ?) so the entity
controls it. I don't know teh best practices to design such entities. I don't
have that much experience designing value object and entities, what they carry,
how they modify their state, and so on.

______________________________________________________________________

## Summary

| # | Location | Category | Impact | Proposed fix |
|---|----------|----------|--------|--------------| | 1 | `ByteTrackTracker` /
`Tracker` Protocol | Hidden contract | High | `TrackerUpdate` return type | | 2
| `Tracker` Protocol / DI | Hidden statefulness | Medium | Scoped factory or
explicit lifecycle | | 3 | `AnalysisProgressionProjection` | ISP violation | Low
| Split Writer/Reader Protocols | | 4 | `Frame.data` numpy | Domain/infra
coupling | Medium | Question intent of `Frame` | | 5 | `batch_size=8` in DI |
Config buried in DI | Low | Move to `Config` | | 6 | `_missed_frames` underscore
| Naming | Low | Remove underscore |
