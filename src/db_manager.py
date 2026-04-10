import sqlite3
from pathlib import Path

from src.models import FileRecord

DB_PATH = Path.home() / ".aifilemanager" / "files.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS files (
    path            TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    extension       TEXT NOT NULL,
    size_bytes      INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'NEW',
    summary         TEXT,
    category        TEXT,
    suggested_name  TEXT,
    error           TEXT,
    analyzed_at     TEXT
)
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_CREATE_TABLE)
    conn.commit()
    return conn


def _row_to_record(row: sqlite3.Row) -> FileRecord:
    return FileRecord(
        path=row["path"],
        name=row["name"],
        extension=row["extension"],
        size_bytes=row["size_bytes"],
        status=row["status"],
        summary=row["summary"],
        category=row["category"],
        suggested_name=row["suggested_name"],
        error=row["error"],
    )


def upsert_records(records: list[FileRecord]) -> None:
    """Insert new records; skip paths that already exist."""
    with _connect() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO files (path, name, extension, size_bytes, status)
            VALUES (:path, :name, :extension, :size_bytes, :status)
            """,
            [
                {
                    "path": r.path,
                    "name": r.name,
                    "extension": r.extension,
                    "size_bytes": r.size_bytes,
                    "status": r.status,
                }
                for r in records
            ],
        )


def get_existing_paths() -> set[str]:
    with _connect() as conn:
        rows = conn.execute("SELECT path FROM files").fetchall()
    return {row["path"] for row in rows}


def get_pending() -> list[FileRecord]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM files WHERE status = 'NEW'"
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def get_all() -> list[FileRecord]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM files ORDER BY analyzed_at DESC NULLS LAST, name ASC"
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def update_record(record: FileRecord) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE files SET
                status         = :status,
                summary        = :summary,
                category       = :category,
                suggested_name = :suggested_name,
                error          = :error,
                analyzed_at    = datetime('now')
            WHERE path = :path
            """,
            {
                "path": record.path,
                "status": record.status,
                "summary": record.summary,
                "category": record.category,
                "suggested_name": record.suggested_name,
                "error": record.error,
            },
        )
