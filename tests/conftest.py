from pathlib import Path

import pytest


@pytest.fixture(scope="function")
def test_data_dir() -> Path:
    return Path(__file__).parent / "data"
