from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileInfo:
    path: Path
    name: str
    extension: str
    size_bytes: int
    created_at: float
    modified_at: float
    is_dir: bool


@dataclass
class ClassificationResult:
    file_info: FileInfo
    file_type: str
    category: str
    subcategory: str
    suggested_name: str
    suggested_path: Path
    action: str  # "rename" | "move" | "rename+move" | "none"
