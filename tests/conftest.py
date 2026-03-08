import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import Database


@pytest.fixture(scope="session")
def db():
    """Provide a database connection for tests."""
    database = Database()
    yield database
