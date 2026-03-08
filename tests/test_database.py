import os
from sqlalchemy import text
from src.database.connection import Database

os.environ["TESTING"] = "1"


def test_database_connection():
    """Ensure we can connect to the test database."""

    db = Database()

    with db.get_session() as session:
        result = session.execute(text("SELECT 1")).scalar()

    assert result == 1
