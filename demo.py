"""
End-to-end demo: retains a real-looking project scope into Hindsight, then
runs the same incoming client message through the agent twice — once with no
memory, once with Hindsight recall — so the difference is visible side by
side.

Usage:
    python demo.py
"""

from dotenv import load_dotenv

from scope_creep_agent.agent import answer_with_memory, answer_without_memory
from scope_creep_agent.data import NEW_CLIENT_MESSAGE, ORIGINAL_SCOPE, PROJECT_ID
from scope_creep_agent.llm import LLM
from scope_creep_agent.memory import ProjectMemory


def main() -> None:
    load_dotenv()

    llm = LLM()
    memory = ProjectMemory()

    print("=" * 70)
    print("STEP 1 — Retaining original project scope into Hindsight")
    print("=" * 70)
    memory.retain_scope(PROJECT_ID, ORIGINAL_SCOPE)
    print(f"Retained scope for project: {PROJECT_ID}\n")

    print("=" * 70)
    print("STEP 2 — New client message comes in")
    print("=" * 70)
    print(NEW_CLIENT_MESSAGE.strip())
    print()

    print("=" * 70)
    print("WITHOUT MEMORY — agent sees only the new message")
    print("=" * 70)
    no_memory_reply = answer_without_memory(llm, NEW_CLIENT_MESSAGE)
    print(no_memory_reply)
    print()

    print("=" * 70)
    print("WITH MEMORY — agent recalls the original scope from Hindsight")
    print("=" * 70)
    with_memory_reply = answer_with_memory(llm, memory, PROJECT_ID, NEW_CLIENT_MESSAGE)
    print(with_memory_reply)
    print()

    memory.close()


if __name__ == "__main__":
    main()
