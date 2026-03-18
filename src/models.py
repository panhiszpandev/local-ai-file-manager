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
    visual_content: Optional[str]
    file_type: str
    category: str
    confidence: float
    alternative_category: Optional[str]
    suggested_name: str
    suggested_path: Path
    action: str  # "rename" | "move" | "rename+move" | "none"
