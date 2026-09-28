"""
Core agent logic.

- answer_without_memory(...)   the LLM sees only the new message
- analyze_with_memory(...)     the LLM sees the new message + Hindsight memories
- answer_with_memory(...)      convenience wrapper returning just the reply
- retain_interaction(...)      stores the request and decision back in Hindsight
"""

from dataclasses import dataclass

from .llm import LLM
from .memory import ProjectMemory


NO_MEMORY_SYSTEM_PROMPT = """
You are a helpful assistant replying to a client message about a web
design project. You have no other information about the project.

Write a short, ready-to-send reply. Do not use placeholders like [Name].
"""


WITH_MEMORY_SYSTEM_PROMPT = """
You are a scope-management assistant for a freelance web design studio.

You will be given:
1. A new client message.
2. Memories recalled from the project's history, including the original
   agreement and possibly earlier requests and decisions.

Your job is to determine the current status of the request using ONLY
the recalled project memories as the source of truth.

Rules:

1. Decide whether the new request is inside or outside the originally
   agreed scope.

2. If the request is outside scope:
   - VERDICT must be OUT_OF_SCOPE.
   - Explain which part of the agreement excludes it.
   - Normally recommend a paid change order.

3. If the request is inside scope:
   - VERDICT must be IN_SCOPE.
   - Confirm that it is within the agreement and respond helpfully.

4. If there is not enough relevant project memory:
   - VERDICT must be UNKNOWN.
   - Do not invent project terms.

5. Track change-order status using the project history:
   - NONE = no change order is relevant.
   - PROPOSED = an out-of-scope change has been identified or proposed,
     but there is no clear approval in the project history.
   - APPROVED = the client clearly approved the proposed change order or
     clearly authorized the previously proposed out-of-scope work.
   - REJECTED = the client clearly rejected the proposed change.

6. If the client says something like "go ahead", "let's do it", or
   "please add it" after a change order was proposed, treat that as
   client authorization for the change unless the memories contain
   information showing that the change was rejected or still requires
   some explicit approval step.

7. Never claim a change order was approved unless the current message or
   recalled project history provides evidence for that.

8. Remember that the original agreement remains important, but later
   documented client decisions can change the current project state.

Output format (strict):

Line 1:
VERDICT: IN_SCOPE
or
VERDICT: OUT_OF_SCOPE
or
VERDICT: UNKNOWN

Line 2:
CHANGE_ORDER: NONE
or
CHANGE_ORDER: PROPOSED
or
CHANGE_ORDER: APPROVED
or
CHANGE_ORDER: REJECTED

Line 3:
REASON: a short explanation of why the request has this verdict.

Line 4:
ACTION: a short recommended next step.

Then a blank line, followed by a short, ready-to-send reply to the client.

Do not use placeholders like [Name].
"""


@dataclass
class Analysis:
    verdict: str
    reply: str
    recalled: str
    change_order_status: str
    reason: str
    recommended_action: str


def parse_analysis(raw: str) -> tuple[str, str, str, str, str]:
    """
    Parse the structured LLM response.

    Returns:
        (verdict, change_order_status, reason, recommended_action, reply)
    """

    lines = raw.strip().splitlines()

    verdict = "UNKNOWN"
    change_order_status = "NONE"
    reason = ""
    recommended_action = ""

    reply_start = 0

    for i, line in enumerate(lines):
        cleaned = line.strip()

        upper = cleaned.upper()

        if upper.startswith("VERDICT:"):
            verdict = (
                cleaned.split(":", 1)[1]
                .strip()
                .upper()
                .replace(" ", "_")
            )
            reply_start = max(reply_start, i + 1)

        elif upper.startswith("CHANGE_ORDER:"):
            change_order_status = (
                cleaned.split(":", 1)[1]
                .strip()
                .upper()
                .replace(" ", "_")
            )
            reply_start = max(reply_start, i + 1)

        elif upper.startswith("REASON:"):
            reason = cleaned.split(":", 1)[1].strip()
            reply_start = max(reply_start, i + 1)

        elif upper.startswith("ACTION:"):
            recommended_action = cleaned.split(":", 1)[1].strip()
            reply_start = max(reply_start, i + 1)

    if verdict not in {"IN_SCOPE", "OUT_OF_SCOPE", "UNKNOWN"}:
        verdict = "UNKNOWN"

    if change_order_status not in {
        "NONE",
        "PROPOSED",
        "APPROVED",
        "REJECTED",
    }:
        change_order_status = "NONE"

    # Skip blank lines after the structured headers.
    while reply_start < len(lines) and not lines[reply_start].strip():
        reply_start += 1

    reply = "\n".join(lines[reply_start:]).strip()

    if not reply:
        reply = raw.strip()

    return (
        verdict,
        change_order_status,
        reason,
        recommended_action,
        reply,
    )


def answer_without_memory(llm: LLM, client_message: str) -> str:
    """Generate a baseline response without project memory."""

    return llm.ask(
        NO_MEMORY_SYSTEM_PROMPT,
        client_message,
    )


def analyze_with_memory(
    llm: LLM,
    memory: ProjectMemory,
    project_id: str,
    client_message: str,
) -> Analysis:
    """Analyze a client request using the project's Hindsight memory."""

    recalled = memory.recall_relevant_scope(
        project_id,
        client_message,
    )

    if recalled:
        user_prompt = (
            f"New client message:\n{client_message}\n\n"
            f"Recalled from the project history:\n{recalled}"
        )
    else:
        user_prompt = (
            f"New client message:\n{client_message}\n\n"
            "No memories were found for this project."
        )

    raw = llm.ask(
        WITH_MEMORY_SYSTEM_PROMPT,
        user_prompt,
    )

    (
        verdict,
        change_order_status,
        reason,
        recommended_action,
        reply,
    ) = parse_analysis(raw)

    return Analysis(
        verdict=verdict,
        reply=reply,
        recalled=recalled,
        change_order_status=change_order_status,
        reason=reason,
        recommended_action=recommended_action,
    )


def answer_with_memory(
    llm: LLM,
    memory: ProjectMemory,
    project_id: str,
    client_message: str,
) -> str:
    """Return only the ready-to-send reply."""

    return analyze_with_memory(
        llm,
        memory,
        project_id,
        client_message,
    ).reply


def retain_interaction(
    memory,
    project_id: str,
    client_message: str,
    analysis: Analysis,
) -> str:
    """Retain the client request and the agent's decision in project memory."""

    interaction = (
        f"Client request:\n{client_message}\n\n"
        f"Agent decision:\n"
        f"Verdict: {analysis.verdict}\n"
        f"Change order status: {analysis.change_order_status}\n"
        f"Reason: {analysis.reason}\n"
        f"Recommended action: {analysis.recommended_action}\n"
        f"Agent reply: {analysis.reply}"
    )

    memory.retain_note(
        project_id,
        interaction,
    )

    return interaction