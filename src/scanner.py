from pathlib import Path

from src.models import FileRecord
from src.csv_manager import read_records, write_records


def scan(root: Path, output_csv: Path) -> list[FileRecord]:
    """Scan directory recursively and write/update CSV with discovered files.

    If CSV already exists, only new files (not yet in CSV) are added.
    Returns the full list of records.
    """
    existing = read_records(output_csv)
    existing_paths = {r.path for r in existing}

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

    all_records = existing + new_records
    write_records(output_csv, all_records)
    return all_records
