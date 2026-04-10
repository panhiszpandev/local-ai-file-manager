import os

MAX_CHARS = 10_000

PLAIN_EXTENSIONS = {".txt", ".md", ".csv", ".html", ".htm", ".xml", ".json", ".log"}

DEFINITION = {
    "type": "function",
    "function": {
        "name": "read_text",
        "description": (
            "Extract text content from a text-based file. "
            "Supports: .txt, .md, .csv, .html, .xml, .json, .log, .docx, .rtf"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file",
                }
            },
            "required": ["path"],
        },
    },
}


def _read_plain(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(MAX_CHARS)


def _read_docx(path: str) -> str:
    from docx import Document

    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs)
    return text[:MAX_CHARS]


def _read_rtf(path: str) -> str:
    from striprtf.striprtf import rtf_to_text

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    text = rtf_to_text(raw)
    return text[:MAX_CHARS]


def handle(path: str) -> str:
    _, ext = os.path.splitext(path)
    ext = ext.lower()

    if ext == ".docx":
        return _read_docx(path)
    elif ext == ".rtf":
        return _read_rtf(path)
    elif ext in PLAIN_EXTENSIONS:
        return _read_plain(path)
    else:
        return _read_plain(path)
