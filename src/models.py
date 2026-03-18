from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
    confidence: float
    alternative_category: Optional[str]
    alternative_subcategory: Optional[str]
    suggested_name: str
    suggested_path: Path
    action: str  # "rename" | "move" | "rename+move" | "none"
