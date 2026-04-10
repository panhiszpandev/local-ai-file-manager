import base64
import io
import os

MAX_CHARS = 10_000
MIN_TEXT_LENGTH = 50

DEFINITION = {
    "type": "function",
    "function": {
        "name": "read_pdf",
        "description": (
            "Extract text content from a PDF file. "
            "Handles both text-based PDFs and scanned PDFs (via vision OCR)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the PDF file",
                }
            },
            "required": ["path"],
        },
    },
}


def _extract_text(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages)[:MAX_CHARS]


def _ocr_via_vision(path: str, llm_client) -> str:
    """Convert scanned PDF pages to images and send to vision model for OCR."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    all_text = []

    for i, page in enumerate(reader.pages[:5]):  # limit to first 5 pages
        images = page.images
        if not images:
            continue

        for img in images:
            image_data = base64.b64encode(img.data).decode("utf-8")
            messages = [
                {"role": "system", "content": "Extract all visible text from this image. Return only the text, no commentary."},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Extract text from page {i + 1} of a scanned PDF:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                ]},
            ]
            response = llm_client.chat(messages)
            text = response.choices[0].message.content or ""
            all_text.append(text.strip())

    return "\n\n".join(all_text)[:MAX_CHARS]


_llm_client = None


def init(llm_client):
    global _llm_client
    _llm_client = llm_client


def handle(path: str) -> str:
    text = _extract_text(path)

    if len(text.strip()) >= MIN_TEXT_LENGTH:
        return text

    if _llm_client is None:
        return text or "PDF appears to be scanned but vision OCR is not available."

    ocr_text = _ocr_via_vision(path, _llm_client)
    if ocr_text.strip():
        return ocr_text

    return text or "Could not extract text from this PDF."
