"""
Wrapper around the Hindsight client, scoped to how this agent uses memory.

Each project gets its own memory bank (bank_id = project_id) so scope memory
never bleeds across clients. This module only exposes exactly the two
operations the agent needs: retain the scope, recall what's relevant to a
new request.
"""

import os

from hindsight_client import Hindsight


class ProjectMemory:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or os.environ.get(
            "HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io"
        )
        self.api_key = api_key or os.environ["HINDSIGHT_API_KEY"]
        self._client = Hindsight(base_url=self.base_url, api_key=self.api_key)

    def _bank_id(self, project_id: str) -> str:
        # One memory bank per project keeps clients' scopes fully isolated.
        return f"scope-creep-{project_id}"

    def retain_scope(self, project_id: str, scope_text: str) -> None:
        """Store the original agreed scope for a project."""
        self._client.retain(bank_id=self._bank_id(project_id), content=scope_text)

    def retain_note(self, project_id: str, note: str) -> None:
        """Store any other project event (a delivered milestone, a prior
        flagged request and how it was resolved, etc.) so the agent keeps
        building context over the life of the project."""
        self._client.retain(bank_id=self._bank_id(project_id), content=note)

    def recall_relevant_scope(self, project_id: str, new_request: str, max_tokens: int = 2048) -> str:
        """
        Recall memories relevant to a new client request. Returns a plain-text
        block the LLM can read directly; empty string if nothing relevant has
        been retained yet (e.g. brand-new project, no scope stored).
        """
        result = self._client.recall(
            bank_id=self._bank_id(project_id),
            query=new_request,
            max_tokens=max_tokens,
        )
        if not result.results:
            return ""
        return "\n".join(f"- [{m.type}] {m.text}" for m in result.results)

    def close(self) -> None:
        self._client.close()
