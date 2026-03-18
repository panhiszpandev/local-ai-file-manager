import base64
from pathlib import Path
from typing import Optional

from src.models import FileInfo

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".heic", ".heif"}


def encode_image(file_info: FileInfo) -> Optional[dict]:
    """Read and encode image as base64, return image_url content part or None on failure."""
    try:
        with open(file_info.path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        mime = "image/png" if file_info.extension == ".png" else "image/jpeg"
        return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}}
    except (OSError, PermissionError):
        return None


def build_user_message(file_info: FileInfo) -> list[dict]:
    """Build the user message for the LLM, including image if applicable."""
    metadata = (
        f"Name: {file_info.name}\n"
        f"Extension: {file_info.extension}\n"
        f"Size: {file_info.size_bytes} bytes\n"
        f"Is directory: {file_info.is_dir}"
    )

    if file_info.extension in IMAGE_EXTENSIONS:
        image_part = encode_image(file_info)
        if image_part:
            return [
                {"type": "text", "text": f"File metadata:\n{metadata}\n\nClassify this file:"},
                image_part,
            ]

    return [{"type": "text", "text": f"File metadata:\n{metadata}\n\nClassify this file:"}]
