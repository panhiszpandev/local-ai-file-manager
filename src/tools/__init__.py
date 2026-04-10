from src.tools import get_file_info, read_text, read_pdf, read_image

TOOL_DEFINITIONS = [
    get_file_info.DEFINITION,
    read_text.DEFINITION,
    read_pdf.DEFINITION,
    read_image.DEFINITION,
]

TOOL_HANDLERS = {
    "get_file_info": get_file_info.handle,
    "read_text": read_text.handle,
    "read_pdf": read_pdf.handle,
    "read_image": read_image.handle,
}


def init_tools(llm_client):
    """Initialize tools that need access to the LLM client (vision-based tools)."""
    read_pdf.init(llm_client)
    read_image.init(llm_client)
