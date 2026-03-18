import json
from pathlib import Path

from openai import OpenAI, BadRequestError

from src.models import FileInfo, ClassificationResult
from src.image_utils import build_user_message
from src.document_analyzer import DocumentAnalyzer, looks_like_document
from src.utils import strip_markdown

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_system_prompt() -> str:
    taxonomy = (_PROMPTS_DIR / "taxonomy.md").read_text(encoding="utf-8")
    template = (_PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    return template.replace("{taxonomy}", taxonomy)


class Classifier:
    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = "qwen2.5-7b-instruct"):
        self.client = OpenAI(base_url=base_url, api_key="lm-studio")
        self.model = model
        self.system_prompt = _load_system_prompt()
        self.document_analyzer = DocumentAnalyzer(self.client, self.model)

    def _fallback_result(self, file_info: FileInfo, scan_root: Path) -> ClassificationResult:
        return ClassificationResult(
            file_info=file_info,
            visual_content=None,
            file_type=file_info.extension or "unknown",
            category="Do przejrzenia",
            confidence=0.0,
            alternative_category=None,
            suggested_name=file_info.name,
            suggested_path=file_info.path.parent,
            action="none",
        )

    def classify(self, file_info: FileInfo, scan_root: Path) -> ClassificationResult:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": build_user_message(file_info)},
                ],
                temperature=0.1,
            )
        except BadRequestError:
            return self._fallback_result(file_info, scan_root)

        raw = strip_markdown(response.choices[0].message.content.strip())

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "file_type": file_info.extension or "unknown",
                "category": "Do przejrzenia",
                "suggested_name": file_info.name,
                "suggested_path": str(file_info.path.parent.relative_to(scan_root)),
                "action": "none",
            }

        visual_content = data.get("visual_content")

        # if image looks like a document, run specialized document analyzer
        if visual_content and looks_like_document(visual_content):
            doc = self.document_analyzer.analyze(visual_content, file_info)
            if doc.get("category"):
                data["category"] = doc["category"]
                data["confidence"] = doc.get("confidence", data.get("confidence", 0.0))

        return ClassificationResult(
            file_info=file_info,
            visual_content=visual_content,
            file_type=data.get("file_type", file_info.extension),
            category=data.get("category", "Do przejrzenia"),
            confidence=float(data.get("confidence", 0.0)),
            alternative_category=data.get("alternative_category"),
            suggested_name=data.get("suggested_name", file_info.name),
            suggested_path=scan_root / (data.get("suggested_path") or ""),
            action=data.get("action", "none"),
        )
