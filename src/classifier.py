import base64
import json
from pathlib import Path

from openai import OpenAI

from src.models import FileInfo, ClassificationResult

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}

SYSTEM_PROMPT = """\
You are a file classification assistant. Given file metadata (and optionally an image preview), \
classify the file and suggest an organized name and path.

Respond ONLY with a valid JSON object using this exact structure:
{
  "file_type": "<extension or 'directory'>",
  "category": "<top-level category>",
  "subcategory": "<subcategory>",
  "suggested_name": "<new filename with extension>",
  "suggested_path": "<relative path from scan root, e.g. images/screenshots>",
  "action": "<none|rename|move|rename+move>"
}
"""


def _build_user_message(file_info: FileInfo) -> list[dict]:
    metadata = (
        f"Name: {file_info.name}\n"
        f"Extension: {file_info.extension}\n"
        f"Size: {file_info.size_bytes} bytes\n"
        f"Is directory: {file_info.is_dir}"
    )

    if file_info.extension in IMAGE_EXTENSIONS:
        try:
            with open(file_info.path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            mime = "image/png" if file_info.extension == ".png" else "image/jpeg"
            return [
                {
                    "type": "text",
                    "text": f"File metadata:\n{metadata}\n\nClassify this file:",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{image_data}"},
                },
            ]
        except (OSError, PermissionError):
            pass

    return [{"type": "text", "text": f"File metadata:\n{metadata}\n\nClassify this file:"}]


class Classifier:
    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = "qwen2.5-7b-instruct"):
        self.client = OpenAI(base_url=base_url, api_key="lm-studio")
        self.model = model

    def classify(self, file_info: FileInfo, scan_root: Path) -> ClassificationResult:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(file_info)},
            ],
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "file_type": file_info.extension or "unknown",
                "category": "unknown",
                "subcategory": "unknown",
                "suggested_name": file_info.name,
                "suggested_path": str(file_info.path.parent.relative_to(scan_root)),
                "action": "none",
            }

        return ClassificationResult(
            file_info=file_info,
            file_type=data.get("file_type", file_info.extension),
            category=data.get("category", "unknown"),
            subcategory=data.get("subcategory", "unknown"),
            suggested_name=data.get("suggested_name", file_info.name),
            suggested_path=scan_root / data.get("suggested_path", ""),
            action=data.get("action", "none"),
        )
