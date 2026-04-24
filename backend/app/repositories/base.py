import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from app.core.exceptions import ConflictError
from app.db.connection import DatabaseSession


class BaseRepository:
    """Shared SQL helpers for repository classes."""

    def __init__(self, session: DatabaseSession) -> None:
        self.session = session

    def _fetch_one(self, query: str, params: Sequence[Any] = ()) -> Optional[sqlite3.Row]:
        return self.session.fetch_one(query, params)

    def _fetch_all(self, query: str, params: Sequence[Any] = ()) -> List[sqlite3.Row]:
        return self.session.fetch_all(query, params)

    def _execute(self, query: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        try:
            return self.session.execute(query, params)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc

    def _executemany(
        self, query: str, params: Iterable[Sequence[Any]]
    ) -> sqlite3.Cursor:
        try:
            return self.session.executemany(query, params)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc

    @staticmethod
    def _build_update_clause(payload: Dict[str, Any]) -> Tuple[str, List[Any]]:
        assignments = []
        values = []
        for column, value in payload.items():
            assignments.append(f"{column} = ?")
            values.append(value)
        return ", ".join(assignments), values
