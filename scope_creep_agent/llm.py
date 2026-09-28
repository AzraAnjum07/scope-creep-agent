"""
Thin wrapper around Groq's OpenAI-compatible chat completions endpoint.

Groq is used purely for reasoning (deciding whether a new client request is
in-scope). Memory itself lives entirely in Hindsight — this module has no
memory of its own.
"""

import os

from openai import OpenAI


class LLM:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or os.environ["GROQ_API_KEY"]
        self.base_url = base_url or os.environ.get(
            "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
        )
        self.model = model or os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def ask(self, system_prompt: str, user_prompt: str, retries: int = 2) -> str:
        """
        Single-turn completion with basic retry handling. The PDF flags that
        recommended Groq models can be flaky with function calling — we're
        not using tool calls here, but we keep the retry loop cheap insurance
        against transient API errors during a live demo.
        """
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:  # noqa: BLE001 - want to retry on anything transient
                last_error = exc
        raise RuntimeError(f"LLM call failed after {retries + 1} attempts") from last_error
