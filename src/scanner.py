from pathlib import Path

from src.db_manager import get_existing_paths, upsert_records
from src.models import FileRecord


def scan(root: Path) -> list[FileRecord]:
    """Scan directory recursively and insert new files into the database.

    Already-known paths are skipped. Returns the list of newly added records.
    """
    existing_paths = get_existing_paths()

    new_records = []
    for entry in root.rglob("*"):
        if any(part.startswith(".") for part in entry.relative_to(root).parts):
            continue
        if entry.is_dir():
            continue

        path_str = str(entry)
        if path_str in existing_paths:
            continue

        try:
            stat = entry.stat()
        except (PermissionError, OSError):
            continue

        new_records.append(FileRecord(
            path=path_str,
            name=entry.name,
            extension=entry.suffix.lower(),
            size_bytes=stat.st_size,
        ))

    if new_records:
        upsert_records(new_records)

    return new_records
