"""
Wrapper around the Hindsight client, scoped to how this agent uses memory.

Each project gets its own memory bank so scope memory never bleeds across
clients.
"""

import os

from hindsight_client import Hindsight


class ProjectMemory:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.base_url = base_url or os.environ.get(
            "HINDSIGHT_BASE_URL",
            "https://api.hindsight.vectorize.io",
        )
        self.api_key = api_key or os.environ["HINDSIGHT_API_KEY"]
        self._client = Hindsight(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def _bank_id(self, project_id: str) -> str:
        """Return the isolated Hindsight bank for a project."""
        return f"scope-creep-{project_id}"

    def bank_id(self, project_id: str) -> str:
        """Return the public Hindsight bank ID for a project."""
        return self._bank_id(project_id)

    def retain_scope(self, project_id: str, scope_text: str) -> None:
        """Store the original agreed scope for a project."""
        self._client.retain(
            bank_id=self._bank_id(project_id),
            content=scope_text,
        )

    def retain_note(self, project_id: str, note: str) -> None:
        """Store a later project event or interaction."""
        self._client.retain(
            bank_id=self._bank_id(project_id),
            content=note,
        )

    def recall_relevant_scope(
        self,
        project_id: str,
        new_request: str,
        max_tokens: int = 2048,
    ) -> str:
        """
        Recall memories relevant to a new client request.

        Returns a plain-text block that the LLM can read directly.
        """
        result = self._client.recall(
            bank_id=self._bank_id(project_id),
            query=new_request,
            max_tokens=max_tokens,
        )

        if not result.results:
            return ""

        return "\n".join(
            f"- [{m.type}] {m.text}"
            for m in result.results
        )

    def recall_project_context(
        self,
        project_id: str,
        query: str = "all client requests, decisions and the original agreement",
        max_tokens: int = 4096,
    ) -> str:
        """
        Recall broader project history for the dashboard.
        """
        return self.recall_relevant_scope(
            project_id,
            query,
            max_tokens=max_tokens,
        )

    def close(self) -> None:
        """Close the Hindsight client."""
        self._client.close()