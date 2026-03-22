import contextlib
from pathlib import Path

import streamlit as st

from vigil.adapters.primary.streamlit.components import api_client
from vigil.adapters.primary.streamlit.components.exceptions import VigilAPIError, VigilConnectionError
from vigil.adapters.primary.streamlit.components.models import VideoEntry, VideoStatus
from vigil.adapters.primary.streamlit.components.video_renderer import render_video_with_tracks

st.set_page_config(
    page_title="Vigil",
    page_icon="🎥",
    layout="wide",
)

# --- State initialisation -----------------------------------------------------------

st.session_state.setdefault("videos", {})  # dict[str, VideoEntry]
st.session_state.setdefault("selected_id", None)  # str | None
st.session_state.setdefault("rendered_path", None)  # Path | None


# --- Helpers ------------------------------------------------------------------------


def _select_video(video_id: str) -> None:
    """Set the given video as the only selected one."""
    st.session_state.selected_id = video_id
    st.session_state.rendered_path = None


def _handle_upload(uploaded_file) -> None:
    """Upload a file to the backend and register it in local state.

    No-op if the file has already been uploaded this session.
    """
    if any(e.name == uploaded_file.name for e in st.session_state.videos.values()):
        return

    file_bytes = uploaded_file.read()
    try:
        video_id = api_client.upload_video(name=uploaded_file.name, data=file_bytes)
    except VigilConnectionError as error:
        st.error(str(error))
        return
    except VigilAPIError as error:
        st.error(str(error))
        return

    st.session_state.videos[video_id] = VideoEntry(video_id=video_id, name=uploaded_file.name, file_bytes=file_bytes)


def _handle_display() -> None:
    """Fetch tracks for the selected video and render the annotated video."""
    video_id = st.session_state.selected_id
    if video_id is None:
        return

    entry: VideoEntry = st.session_state.videos[video_id]

    try:
        tracks = api_client.get_tracks(video_id)
        rendered_path = render_video_with_tracks(video_bytes=entry.file_bytes, tracks=tracks)
    except VigilAPIError as error:
        st.error(str(error))
        return
    except Exception as error:
        st.error(f"Rendering failed: {error}")
        return

    st.session_state.rendered_path = rendered_path


# --- Background status poller -------------------------------------------------------


@st.fragment(run_every=2)
def _status_poller() -> None:
    """Poll pending videos every 2 s and trigger a full rerun on any change.

    Renders no visible widgets — side-effects only.
    """
    for entry in st.session_state.get("videos", {}).values():
        if entry.status is not None and entry.status.is_complete:
            continue
        previous = entry.status.analysed_frames if entry.status else -1
        with contextlib.suppress(VigilAPIError):
            entry.status = api_client.get_status(entry.video_id)
        current = entry.status.analysed_frames if entry.status else -1
        if current != previous:
            st.rerun()


# --- Layout -------------------------------------------------------------------------

st.title("🎥 Vigil")

_status_poller()

left, right = st.columns([1, 2], gap="large")

with left:
    uploaded = st.file_uploader(
        "Upload a video",
        type=[
            "mp4",
        ],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        _handle_upload(uploaded)

    st.divider()

    videos: dict[str, VideoEntry] = st.session_state.videos

    if not videos:
        st.caption("No videos uploaded yet.")
    else:
        for entry in videos.values():
            col_name, col_status = st.columns([4, 1], gap="small")
            with col_name:
                st.write(entry.name)
            with col_status:
                status: VideoStatus | None = entry.status
                is_done = status is not None and status.is_complete
                if is_done:
                    is_selected = st.session_state.selected_id == entry.video_id
                    if st.checkbox(
                        label=entry.name,
                        value=is_selected,
                        key=f"chk_{entry.video_id}",
                        label_visibility="collapsed",
                    ):
                        if not is_selected:
                            _select_video(entry.video_id)
                    elif is_selected:
                        st.session_state.selected_id = None
                        st.session_state.rendered_path = None
                else:
                    if status is not None and status.total_frames > 0:
                        pct = int(100 * status.analysed_frames / status.total_frames)
                        st.progress(pct / 100, text=f"{pct}%")
                    else:
                        st.caption("queued…")

    st.divider()

    selected_id = st.session_state.selected_id
    display_disabled = selected_id is None or selected_id not in videos
    if st.button("Display", disabled=display_disabled, use_container_width=True):
        _handle_display()

with right:
    rendered_path: Path | None = st.session_state.rendered_path
    if rendered_path is not None and rendered_path.exists():
        st.video(str(rendered_path))
    else:
        st.markdown(
            """
            <div style="
                height: 400px;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 2px dashed #ccc;
                border-radius: 12px;
                color: #aaa;
                font-size: 1.1rem;
            ">
                Select a processed video and click <strong>&nbsp;Display&nbsp;</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
