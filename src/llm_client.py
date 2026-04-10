from __future__ import annotations

import os

from openai import OpenAI, BadRequestError


class LLMClient:
    def __init__(self, base_url: str, model: str, api_key: str | None = None):
        api_key = api_key or os.getenv("LLM_API_KEY", "lm-studio")
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def chat(self, messages: list[dict], tools: list[dict] | None = None, temperature: float = 0.1):
        """Send a chat completion request. Returns the full response object.

        When tools are provided, the response may contain tool_calls
        that the caller should handle.
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        return self.client.chat.completions.create(**kwargs)
