"""Database connection helper for the project.

This module provides a `Database` class that encapsulates the SQLAlchemy engine
and session creation logic. The class exposes a context manager method
`get_session()` that yields a SQLAlchemy Session and ensures the session is
closed after use to prevent connection leaks.

WARNING: For demonstration purposes this file contains a hard-coded connection
string to the Render-hosted PostgreSQL database as requested. In production
systems, secrets must be stored in environment variables or a secrets manager.

Time complexity: creating the engine is O(1). Acquiring a session is O(1).
Space complexity: O(1) for the connection object.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Database:
    """Encapsulates the SQLAlchemy engine and session factory.

    Attributes:
        engine: SQLAlchemy Engine used for connections.
        SessionLocal: a sessionmaker factory bound to the engine.

    Notes:
        - The Render connection string is hard-coded below per user request.
        - Sessions created via `get_session()` must be closed; the context
          manager ensures that by committing/rolling back and closing.
    """

    # Hard-coded Render Postgres connection string. Replace with the actual
    # connection string provided by Render. Example format:
    # postgresql://<user>:<password>@<host>:<port>/<dbname>
    _RENDER_CONNECTION = "postgresql://admin:wpyaKUJEAyK6SV1fDeIRXqQD1kI6Lciz@dpg-d66db2buibrs73e4uu60-a.ohio-postgres.render.com/steelworks_l12w"

    def __init__(self, connection_string: str | None = None):
        # Use provided connection string or fall back to the hard-coded one.
        self._connection_string = connection_string or self._RENDER_CONNECTION

        # Create engine with reasonable defaults. `future=True` enables
        # SQLAlchemy 2.0 style usage where applicable. Pooling defaults are
        # left in place; tuning may be required for production workloads.
        self.engine = create_engine(self._connection_string, future=True)

        # sessionmaker configured to not expire objects on commit which is
        # convenient for read-after-write within the same transactional scope.
        # Setting `expire_on_commit=False` prevents DetachedInstanceError when
        # objects are accessed after the session has been committed/closed.
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False)

    @contextmanager
    def get_session(self):
        """Context manager that yields a SQLAlchemy Session and ensures
        proper cleanup.

        Yields:
            Session: a SQLAlchemy ORM session object.

        Ensures:
            - The session is committed if no exception occurs.
            - The session is rolled back on exception.
            - The session is closed no matter what to prevent connection leaks.

        Time complexity: O(1) to create/close a session.
        Space complexity: O(1) for session object.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            # Rollback to keep DB consistent and re-raise the exception for
            # higher-level handlers/logging.
            session.rollback()
            raise
        finally:
            # Closing the session returns the connection to the pool and
            # frees resources. This prevents connection leaks.
            session.close()


# Create a module-level default database instance for convenience. Tests or
# other modules can instantiate `Database` with a different connection string
# if needed.
default_db = Database()
