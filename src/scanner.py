import os
from pathlib import Path
from typing import Iterator

from src.models import FileInfo


def scan(root: Path) -> Iterator[FileInfo]:
    for entry in root.rglob("*"):
        try:
            stat = entry.stat()
        except (PermissionError, OSError):
            continue

        yield FileInfo(
            path=entry,
            name=entry.name,
            extension=entry.suffix.lower() if not entry.is_dir() else "",
            size_bytes=stat.st_size,
            created_at=stat.st_birthtime,
            modified_at=stat.st_mtime,
            is_dir=entry.is_dir(),
        )
