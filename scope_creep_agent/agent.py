"""
Core agent logic. Two entry points, deliberately kept side by side so the
before/after contrast in the demo is literal, not simulated:

  - answer_without_memory(...)  — the LLM sees only the new message
  - answer_with_memory(...)     — the LLM also sees what Hindsight recalled
"""

from .llm import LLM
from .memory import ProjectMemory

NO_MEMORY_SYSTEM_PROMPT = """\
You are a helpful project assistant for a freelance web design studio.
A client has sent a new message about their ongoing project. Reply
helpfully and professionally.
"""

WITH_MEMORY_SYSTEM_PROMPT = """\
You are a scope-management assistant for a freelance web design studio.
You will be given a new client message, plus memories recalled from the
original project agreement.

Your job:
1. Determine whether the new request falls inside or outside the originally
   agreed scope, using ONLY the recalled memories as the source of truth.
2. If it's outside scope, say so clearly and politely, cite the specific
   part of the original agreement that excludes it, and suggest it be
   handled as a paid change order rather than folded in for free.
3. If it's inside scope, confirm that plainly and proceed helpfully.

Be concrete. Reference the original agreement, don't just say "that wasn't
included."
"""


def answer_without_memory(llm: LLM, client_message: str) -> str:
    return llm.ask(NO_MEMORY_SYSTEM_PROMPT, client_message)


def answer_with_memory(llm: LLM, memory: ProjectMemory, project_id: str, client_message: str) -> str:
    recalled = memory.recall_relevant_scope(project_id, client_message)

    if not recalled:
        # Nothing retained yet for this project — fall back honestly rather
        # than pretending to know the scope.
        user_prompt = (
            f"New client message:\n{client_message}\n\n"
            "No original scope memories were found for this project."
        )
    else:
        user_prompt = (
            f"New client message:\n{client_message}\n\n"
            f"Recalled from the original project agreement:\n{recalled}"
        )

    return llm.ask(WITH_MEMORY_SYSTEM_PROMPT, user_prompt)
