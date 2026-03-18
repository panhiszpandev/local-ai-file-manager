import csv
from pathlib import Path
from typing import Iterable

from src.models import ClassificationResult

FIELDNAMES = [
    "old_path",
    "old_name",
    "new_name",
    "new_path",
    "file_type",
    "category",
    "subcategory",
    "confidence",
    "alternative_category",
    "alternative_subcategory",
    "action",
    "size_bytes",
    "is_dir",
]


def write_csv(results: Iterable[ClassificationResult], output_path: Path) -> int:
    count = 0
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "old_path": str(r.file_info.path),
                "old_name": r.file_info.name,
                "new_name": r.suggested_name,
                "new_path": str(r.suggested_path / r.suggested_name),
                "file_type": r.file_type,
                "category": r.category,
                "subcategory": r.subcategory,
                "confidence": f"{r.confidence:.2f}",
                "alternative_category": r.alternative_category or "",
                "alternative_subcategory": r.alternative_subcategory or "",
                "action": r.action,
                "size_bytes": r.file_info.size_bytes,
                "is_dir": r.file_info.is_dir,
            })
            count += 1
    return count
