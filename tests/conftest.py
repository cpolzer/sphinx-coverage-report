import pathlib
import pytest


@pytest.fixture
def fixture_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "fixtures"
