def strip_markdown(raw: str) -> str:
    """Strip markdown code block wrapper from LLM response."""
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()
