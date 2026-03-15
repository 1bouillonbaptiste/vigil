# Quickstart: Video Analysis Report (001-video-analysis)

**Phase**: 1 — Design
**Date**: 2026-03-15

This guide validates that the fully implemented feature works end-to-end.
Run these steps in order after completing all implementation tasks.

---

## Prerequisites

- Python 3.13+ installed
- Poetry installed (`pip install poetry`)
- A short MP4 test video (≤5 minutes) available locally

---

## 1. Install Dependencies

```bash
poetry install
```

Verify YOLO model weights download on first run (requires internet access):

```bash
poetry run python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

---

## 2. Start the API

```bash
poetry run uvicorn vigil.adapters.primary.api.app:app --reload --port 8000
```

Expected output:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 3. Analyse a Video

Replace `/path/to/test.mp4` with your test video path:

```bash
curl -s -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"video_path": "/path/to/test.mp4"}' | python3 -m json.tool
```

**Expected**: JSON response with `video_id` and `track_summaries` array.

Verify:
- [ ] Response is valid JSON
- [ ] `video_id` is a UUID string
- [ ] `track_summaries` is an array (may be empty for a blank scene)
- [ ] Each entry has `track_id`, `object_class`, `first_frame_index`,
      `last_frame_index`, `first_bbox`, `last_bbox`, `thumbnail_detection_id`
- [ ] `object_class` is either `"person"` or `"vehicle"`

---

## 4. Retrieve the Same Report (No Re-processing)

Copy the `video_id` from the step above:

```bash
VIDEO_ID="<paste-video_id-here>"
curl -s http://localhost:8000/reports/$VIDEO_ID | python3 -m json.tool
```

Verify:
- [ ] Response is identical to the POST /analyse response
- [ ] Server logs show no re-processing (no YOLO inference output)

---

## 5. Error Cases

### 5a. Video Not Found

```bash
curl -s -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"video_path": "/nonexistent/video.mp4"}'
```

Expected: `400` response with a readable error message.

### 5b. Video Exceeds 5 Minutes

Use a video longer than 5 minutes (or create a dummy long video):

```bash
curl -s -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"video_path": "/path/to/long_video.mp4"}'
```

Expected: `422` response mentioning the duration limit.

### 5c. Unknown Video ID

```bash
curl -s http://localhost:8000/reports/00000000-0000-0000-0000-000000000000
```

Expected: `404` response.

---

## 6. Run All Tests

```bash
# Unit tests (no I/O, fast)
poetry run pytest tests/unit/ -v

# Integration tests (requires test fixtures)
poetry run pytest tests/integration/ -v -m integration

# Full suite
poetry run pytest -v
```

Verify:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No ruff lint errors: `poetry run ruff check .`

---

## 7. Validate Report File on Disk

Reports are written to `reports/` at the repository root:

```bash
ls reports/
cat reports/<video_id>.json | python3 -m json.tool
```

Verify:
- [ ] File exists named `<video_id>.json`
- [ ] Contents match the API response
