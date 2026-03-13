"""Database connection helper for the project.

Loads database connection strings from environment variables using python-dotenv.
Uses .env for normal execution and .env.test when running tests.
"""

import logging
import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def load_environment():
    """
    Loads the correct environment file depending on whether tests are running.
    """
    if os.getenv("TESTING"):
        load_dotenv(".env.test")
        logger.debug("load_environment: using .env.test")
    else:
        load_dotenv(".env")
        logger.debug("load_environment: using .env")


class Database:
    """Encapsulates SQLAlchemy engine and session creation."""

    def __init__(self, connection_string: str | None = None):

        # Load environment variables
        load_environment()

        # Use passed connection string or fallback to env variable
        self._connection_string = connection_string or os.getenv("DATABASE_URL")

        if not self._connection_string:
            logger.error("DATABASE_URL is not set in environment variables")
            raise ValueError("DATABASE_URL is not set in environment variables.")

        logger.debug("Database: creating engine")
        self.engine = create_engine(self._connection_string, future=True)

        self.SessionLocal = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )

    @contextmanager
    def get_session(self):
        """Provide a transactional session."""
        session = self.SessionLocal()

        try:
            yield session
            session.commit()

        except Exception:
            session.rollback()
            logger.exception("Session rollback after error")
            raise

        finally:
            session.close()


# Default database instance
default_db = Database()
