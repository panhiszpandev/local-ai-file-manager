import csv
import tempfile
import shutil
from pathlib import Path

from src.models import FileRecord

FIELDNAMES = [
    "path",
    "name",
    "extension",
    "size_bytes",
    "status",
    "summary",
    "category",
    "suggested_name",
    "error",
]


def _record_to_row(record: FileRecord) -> dict:
    return {
        "path": record.path,
        "name": record.name,
        "extension": record.extension,
        "size_bytes": record.size_bytes,
        "status": record.status,
        "summary": record.summary or "",
        "category": record.category or "",
        "suggested_name": record.suggested_name or "",
        "error": record.error or "",
    }


def _row_to_record(row: dict) -> FileRecord:
    return FileRecord(
        path=row["path"],
        name=row["name"],
        extension=row["extension"],
        size_bytes=int(row["size_bytes"]),
        status=row["status"],
        summary=row["summary"] or None,
        category=row["category"] or None,
        suggested_name=row["suggested_name"] or None,
        error=row["error"] or None,
    )


def read_records(csv_path: Path) -> list[FileRecord]:
    if not csv_path.exists():
        return []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [_row_to_record(row) for row in reader]


def read_pending(csv_path: Path) -> list[FileRecord]:
    return [r for r in read_records(csv_path) if r.status == "NEW"]


def write_records(csv_path: Path, records: list[FileRecord]) -> int:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(_record_to_row(record))
    return len(records)


def update_record(csv_path: Path, updated: FileRecord) -> None:
    """Update a single record in the CSV by matching on path. Uses atomic write."""
    records = read_records(csv_path)
    for i, record in enumerate(records):
        if record.path == updated.path:
            records[i] = updated
            break

    tmp = tempfile.NamedTemporaryFile(
        mode="w", newline="", encoding="utf-8",
        dir=csv_path.parent, suffix=".tmp", delete=False,
    )
    try:
        writer = csv.DictWriter(tmp, fieldnames=FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(_record_to_row(record))
        tmp.close()
        shutil.move(tmp.name, csv_path)
    except Exception:
        tmp.close()
        Path(tmp.name).unlink(missing_ok=True)
        raise
