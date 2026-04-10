import json
from pathlib import Path

from src.llm_client import LLMClient
from src.models import FileRecord
from src.tools import TOOL_DEFINITIONS, TOOL_HANDLERS
from src.utils import strip_markdown

_PROMPTS_DIR = Path(__file__).parent / "prompts"

MAX_TOOL_CALLS = 10
MAX_EMPTY_RETRIES = 2


def _load_system_prompt() -> str:
    taxonomy = (_PROMPTS_DIR / "taxonomy.md").read_text(encoding="utf-8")
    template = (_PROMPTS_DIR / "agent_system.md").read_text(encoding="utf-8")
    return template.replace("{taxonomy}", taxonomy)


class Agent:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.system_prompt = _load_system_prompt()

    def process(self, record: FileRecord) -> FileRecord:
        """Process a single file through the tool-calling loop.

        Returns an updated FileRecord with status DONE or FAILED.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Analyze this file: {record.path}"},
        ]

        iterations = 0
        empty_retries = 0
        while iterations < MAX_TOOL_CALLS:
            try:
                response = self.llm.chat(messages, tools=TOOL_DEFINITIONS)
            except Exception as e:
                record.status = "FAILED"
                record.error = f"LLM request failed: {e}"
                return record

            message = response.choices[0].message

            if not message.tool_calls:
                content = (message.content or "").strip()
                if not content and empty_retries < MAX_EMPTY_RETRIES:
                    empty_retries += 1
                    messages.append({"role": "user", "content": "You returned an empty response. Please provide your analysis as a JSON object with summary, category, and suggested_name."})
                    continue
                return self._parse_result(record, content)

            messages.append(message)

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                handler = TOOL_HANDLERS.get(name)

                if handler is None:
                    tool_result = f"Unknown tool: {name}"
                else:
                    try:
                        args = json.loads(tool_call.function.arguments)
                        tool_result = handler(**args)
                    except Exception as e:
                        tool_result = f"Tool error: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

            iterations += 1

        record.status = "FAILED"
        record.error = f"Exceeded maximum tool calls ({MAX_TOOL_CALLS})"
        return record

    def _parse_result(self, record: FileRecord, content: str) -> FileRecord:
        """Parse the agent's final JSON response into the FileRecord."""
        raw = strip_markdown(content.strip())
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            record.status = "FAILED"
            record.error = f"Invalid JSON response: {content[:200]}"
            return record

        record.status = "DONE"
        record.summary = data.get("summary")
        record.category = data.get("category")
        record.suggested_name = data.get("suggested_name")
        return record
