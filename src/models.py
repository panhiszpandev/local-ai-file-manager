from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FileRecord:
    path: str
    name: str
    extension: str
    size_bytes: int
    status: str = "NEW"
    summary: str | None = None
    category: str | None = None
    suggested_name: str | None = None
    error: str | None = None
