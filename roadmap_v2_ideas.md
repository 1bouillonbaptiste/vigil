# V2 — Natural Language Track Query: Design Ideas

## Overview

The user submits a text description (e.g. "man with yellow t-shirt") and gets
back the tracks from a video that best match it. V1 domain and infrastructure
remain unchanged — V2 is purely additive.

______________________________________________________________________

## Two distinct operations

### 1. Indexing (once per analysis, after completion)

**Use case: `EmbedTrack`**

Given a track, reads the representative crop (frame image seeked to
`frame_position`, cropped to `BoundingBox`), computes a vector embedding, and
persists it alongside the track.

Triggered by a new `AnalysisCompleted` domain event. A subscriber calls
`EmbedTrack` for each track produced by the analysis. This fits naturally into
the existing event-driven infrastructure — no changes to the analysis workflow.

Gateways needed:

- `EmbeddingModel` — takes a raw image crop, returns a float vector
- `TrackEmbeddingStore` (write side) — stores `(track_id, vector)`

### 2. Querying (per user request)

**Use case: `QueryTracksByDescription`**

Takes a `video_id` and a natural language `description`. Embeds the text query
using the same `EmbeddingModel` (CLIP handles both image and text encoding),
queries the `TrackEmbeddingStore` for the most similar track vectors, returns
ranked tracks.

Gateways needed:

- `EmbeddingModel` — same adapter as above, text → vector
- `TrackEmbeddingStore` (read side) — similarity search returning ranked
  `track_id` list

______________________________________________________________________

## Gateways

### `EmbeddingModel`

```
embed_image(image: RawImage) -> Vector
embed_text(text: str) -> Vector
```

One adapter (CLIP) implements both methods. Image and text share the same
embedding space, making cosine similarity meaningful across modalities.

### `TrackEmbeddingStore`

```
save(track_id: TrackId, vector: Vector) -> None
find_similar(vector: Vector, video_id: VideoId, top_k: int) -> list[TrackId]
```

In-memory implementation for tests. Production adapter: a vector database (e.g.
Qdrant, ChromaDB) or pgvector if a Postgres store is introduced later.

______________________________________________________________________

## Event flow

```
AnalysisCompleted
    └── EmbedTracksSubscriber
            └── EmbedTrack (use case) × N tracks
                    └── TrackEmbeddingStore.save(track_id, vector)
```

`AnalysisCompleted` is a new domain event emitted by the analysis workflow once
all frames have been processed. The subscriber iterates the track list and calls
`EmbedTrack` for each one.

______________________________________________________________________

## API surface

```
GET /videos/{id}/tracks?description=man+with+yellow+t-shirt
```

Returns the same track schema as `GET /videos/{id}/tracks`, filtered and ranked
by similarity to the description. The endpoint delegates to
`QueryTracksByDescription`; no new domain models leak into the API layer.

______________________________________________________________________

## Prerequisite: frame serving

`EmbedTrack` needs raw pixel data for the crop. This requires resolving the open
question from V1:

- **Option A — backend re-reads the video file on demand.** Clean separation;
  requires the original video file to remain accessible after ingestion.
  Introduces a `FrameReader` gateway (seek to position, return raw image).
  Reintroduces a form of `FrameRepository` but with a read-only, on-demand
  interface rather than a write-all-then-read pattern.

- **Option B — frames are stored as part of analysis.** The `FrameAnalyzed`
  event subscriber stores the raw frame to disk or object storage. A later
  `EmbedTrack` call reads from that store. More storage cost; simpler retrieval.

Option A is preferred: it avoids storing every frame and aligns with the
existing event-driven design. The `FrameReader` gateway is a new port with no
domain coupling.

______________________________________________________________________

## Suggested roadmap steps

1. Resolve the frame-serving question and implement `FrameReader` (OpenCV
   adapter).
1. Introduce `AnalysisCompleted` domain event.
1. `EmbeddingModel` gateway + CLIP adapter.
1. `TrackEmbeddingStore` gateway + in-memory adapter.
1. `EmbedTrack` use case + `EmbedTracksSubscriber`.
1. `QueryTracksByDescription` use case.
1. Extend `GET /videos/{id}/tracks` with optional `description` query parameter.
