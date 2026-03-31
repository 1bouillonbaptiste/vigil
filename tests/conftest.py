from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def test_data_dir() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def realistic_video_filepath(test_data_dir: Path) -> Path:
    """Return the path to the realistic 10-frame people video fixture."""
    return test_data_dir / "people_10frames.mp4"
