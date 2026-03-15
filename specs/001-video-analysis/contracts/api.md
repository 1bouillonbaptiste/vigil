# API Contract: Video Analysis Report (001-video-analysis)

**Phase**: 1 — Design
**Date**: 2026-03-15
**Base URL**: `http://localhost:8000` (development)

---

## POST /analyse

Submits a recorded video for analysis. Runs synchronously; the response is
returned once analysis is complete.

### Request

```
POST /analyse
Content-Type: application/json
```

```json
{
  "video_path": "/absolute/path/to/video.mp4"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `video_path` | string | yes | Absolute path to the video file on the server filesystem |

### Response — 200 OK

```json
{
  "video_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "track_summaries": [
    {
      "track_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "object_class": "person",
      "first_frame_index": 0,
      "last_frame_index": 45,
      "first_bbox": {
        "center_x": 120,
        "center_y": 210,
        "width": 52,
        "height": 130
      },
      "last_bbox": {
        "center_x": 890,
        "center_y": 215,
        "width": 50,
        "height": 128
      },
      "thumbnail_detection_id": "a0b1c2d3-e4f5-6789-abcd-ef0123456789"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `video_id` | UUID string | Stable identifier for this video; use to retrieve later |
| `track_summaries` | array | One entry per tracked object (may be empty) |
| `track_summaries[].track_id` | UUID string | Unique identifier for this track |
| `track_summaries[].object_class` | `"person"` or `"vehicle"` | Detected object class |
| `track_summaries[].first_frame_index` | integer | Frame index in the source video when the object first appeared |
| `track_summaries[].last_frame_index` | integer | Frame index when the object last appeared |
| `track_summaries[].first_bbox` | object | Bounding box at first appearance |
| `track_summaries[].last_bbox` | object | Bounding box at last appearance |
| `track_summaries[].thumbnail_detection_id` | UUID string | ID of the most representative detection (highest visibility score) |

### Response — 400 Bad Request

Video file not found at the given path, or the file cannot be decoded.

```json
{
  "detail": "Video file not found or unreadable: /path/to/video.mp4"
}
```

### Response — 422 Unprocessable Entity

Video exceeds the 5-minute duration limit.

```json
{
  "detail": "Video duration exceeds the 5-minute limit (actual: 7m 12s)"
}
```

---

## GET /reports/{video_id}

Retrieves a previously completed analysis report without re-processing the video.

### Request

```
GET /reports/{video_id}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `video_id` | UUID string (path) | The `video_id` returned by a prior `POST /analyse` call |

### Response — 200 OK

Same schema as `POST /analyse` 200 response.

### Response — 404 Not Found

No analysis report exists for the given `video_id`.

```json
{
  "detail": "No report found for video_id 3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

---

## Notes

- The API is synchronous for v1. The operator blocks until analysis completes.
- No authentication is required in v1.
- `video_path` must be an absolute filesystem path accessible to the Vigil
  process. File upload over HTTP is out of scope for v1.
- Object filtering (fewer than 5 detections per track) is applied automatically;
  the response only includes valid tracks.
