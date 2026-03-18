import json
from pathlib import Path

from openai import OpenAI

from src.models import FileInfo
from src.image_utils import IMAGE_EXTENSIONS, encode_image
from src.utils import strip_markdown

_PROMPTS_DIR = Path(__file__).parent / "prompts"

_DOCUMENT_KEYWORDS = {
    "document", "letter", "form", "invoice", "receipt", "certificate", "contract",
    "report", "printed", "handwritten", "official", "stamp", "signature", "text",
    "heading", "paragraph", "table", "bill", "statement", "application", "notice",
    "agreement", "prescription", "referral", "ticket", "boarding", "warrant",
    "decree", "resolution", "policy", "id card", "passport", "payslip", "tax",
}


def looks_like_document(visual_content: str) -> bool:
    text = visual_content.lower()
    return any(keyword in text for keyword in _DOCUMENT_KEYWORDS)


class DocumentAnalyzer:
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model
        self.prompt = (_PROMPTS_DIR / "document_analyzer.md").read_text(encoding="utf-8")

    def analyze(self, visual_content: str, file_info: FileInfo) -> dict:
        """Specialized vision call: identifies document type from description + fresh image."""
        image_part = encode_image(file_info) if file_info.extension in IMAGE_EXTENSIONS else None

        if image_part:
            user_content = [
                {"type": "text", "text": f"Initial description of the image:\n{visual_content}\n\nNow look at the image yourself and identify the exact document type:"},
                image_part,
            ]
        else:
            user_content = f"Visual description:\n{visual_content}\n\nIdentify the document type and classify it."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
            )
        except Exception:
            if not isinstance(user_content, str):
                # image call failed — retry with text-only description
                user_content = f"Visual description:\n{visual_content}\n\nIdentify the document type and classify it."
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": self.prompt},
                            {"role": "user", "content": user_content},
                        ],
                        temperature=0.1,
                    )
                except Exception:
                    return {}
            else:
                return {}

        raw = strip_markdown(response.choices[0].message.content.strip())
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
