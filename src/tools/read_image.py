import base64
import os

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}

DEFINITION = {
    "type": "function",
    "function": {
        "name": "read_image",
        "description": (
            "Analyze an image file using vision and return a text description of its contents. "
            "Supports: .jpg, .jpeg, .png, .gif, .bmp, .webp, .tiff"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the image file",
                }
            },
            "required": ["path"],
        },
    },
}

_llm_client = None


def init(llm_client):
    global _llm_client
    _llm_client = llm_client


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def handle(path: str) -> str:
    if _llm_client is None:
        return "Vision model not available."

    _, ext = os.path.splitext(path)
    mime = "image/png" if ext.lower() == ".png" else "image/jpeg"

    image_data = _encode_image(path)
    messages = [
        {
            "role": "system",
            "content": (
                "Describe the contents of this image in detail. "
                "If it contains a document, extract all visible text. "
                "If it is a photo, describe what is depicted."
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this image:"},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}},
            ],
        },
    ]
    response = _llm_client.chat(messages)
    return response.choices[0].message.content or "Could not analyze image."
