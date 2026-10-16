import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session")
def spark(tmp_path_factory):
    from caselake.local_demo import local_spark
    session = local_spark(tmp_path_factory.mktemp("spark"), os.getenv("CASELAKE_DELTA_JARS"))
    yield session
    session.stop()
