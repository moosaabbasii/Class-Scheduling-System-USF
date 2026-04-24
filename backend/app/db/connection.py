from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
import sqlite3
from typing import Any, Iterable, List, Optional, Sequence


class DatabaseSession(AbstractContextManager):
    """Thin OO wrapper around a SQLite connection."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = str(database_path)
        self.connection: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "DatabaseSession":
        # FastAPI may finalize sync-yield dependencies in a different worker thread.
        # Allow this per-request connection to be committed/closed across threads.
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON;")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.connection is None:
            return
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()
        self.connection = None

    def fetch_one(
        self, query: str, params: Sequence[Any] = ()
    ) -> Optional[sqlite3.Row]:
        return self._execute_cursor(query, params).fetchone()

    def fetch_all(self, query: str, params: Sequence[Any] = ()) -> List[sqlite3.Row]:
        return self._execute_cursor(query, params).fetchall()

    def execute(self, query: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        return self._execute_cursor(query, params)

    def executemany(
        self, query: str, params: Iterable[Sequence[Any]]
    ) -> sqlite3.Cursor:
        if self.connection is None:
            raise RuntimeError("Database session is not open.")
        return self.connection.executemany(query, params)

    def _execute_cursor(
        self, query: str, params: Sequence[Any] = ()
    ) -> sqlite3.Cursor:
        if self.connection is None:
            raise RuntimeError("Database session is not open.")
        return self.connection.execute(query, params)


class DatabaseManager:
    """Factory for short-lived SQLite sessions."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def session(self) -> DatabaseSession:
        return DatabaseSession(self.database_path)
