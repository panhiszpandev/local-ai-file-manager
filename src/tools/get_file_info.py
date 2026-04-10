import mimetypes
import os
from datetime import datetime

DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_file_info",
        "description": "Get metadata about a file: name, extension, size, dates, and MIME type.",
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


def handle(path: str) -> str:
    stat = os.stat(path)
    name = os.path.basename(path)
    _, ext = os.path.splitext(name)
    mime, _ = mimetypes.guess_type(path)

    return (
        f"Name: {name}\n"
        f"Extension: {ext.lower()}\n"
        f"Size: {stat.st_size} bytes\n"
        f"MIME type: {mime or 'unknown'}\n"
        f"Created: {datetime.fromtimestamp(stat.st_birthtime)}\n"
        f"Modified: {datetime.fromtimestamp(stat.st_mtime)}"
    )
