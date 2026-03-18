import base64
import json
from pathlib import Path

from openai import OpenAI

from src.models import FileInfo, ClassificationResult

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_system_prompt() -> str:
    taxonomy = (_PROMPTS_DIR / "taxonomy.md").read_text(encoding="utf-8")
    template = (_PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    return template.replace("{taxonomy}", taxonomy)


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
        self.system_prompt = _load_system_prompt()

    def classify(self, file_info: FileInfo, scan_root: Path) -> ClassificationResult:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": _build_user_message(file_info)},
            ],
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()

        # strip markdown code block if model wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "file_type": file_info.extension or "unknown",
                "category": "Do przejrzenia",
                "subcategory": "Niepewne",
                "suggested_name": file_info.name,
                "suggested_path": str(file_info.path.parent.relative_to(scan_root)),
                "action": "none",
            }

        return ClassificationResult(
            file_info=file_info,
            file_type=data.get("file_type", file_info.extension),
            category=data.get("category", "Do przejrzenia"),
            subcategory=data.get("subcategory", "Niepewne"),
            confidence=float(data.get("confidence", 0.0)),
            alternative_category=data.get("alternative_category"),
            alternative_subcategory=data.get("alternative_subcategory"),
            suggested_name=data.get("suggested_name", file_info.name),
            suggested_path=scan_root / data.get("suggested_path", ""),
            action=data.get("action", "none"),
        )
