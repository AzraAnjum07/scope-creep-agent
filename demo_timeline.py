"""
Timeline demo: the agent handles three client messages over a project's life.
After each one it retains what happened, so later answers can draw on earlier
interactions, not just the original scope.

Usage:
    python demo_timeline.py
"""

import time

from dotenv import load_dotenv

from scope_creep_agent.agent import answer_with_memory, answer_without_memory
from scope_creep_agent.data import ORIGINAL_SCOPE, PROJECT_ID, TIMELINE
from scope_creep_agent.llm import LLM
from scope_creep_agent.memory import ProjectMemory

# Hindsight processes retained content in the background (fact extraction),
# so give it a moment before we recall something we just retained.
PROCESSING_WAIT_SECONDS = 8


def banner(text: str) -> None:
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def main() -> None:
    load_dotenv()
    llm = LLM()
    memory = ProjectMemory()

    banner("KICKOFF: retaining original scope into Hindsight")
    memory.retain_scope(PROJECT_ID, ORIGINAL_SCOPE)
    time.sleep(PROCESSING_WAIT_SECONDS)

    for step in TIMELINE:
        banner(step["label"])
        print("CLIENT:", step["message"], "\n")

        if step["show_baseline"]:
            print("--- WITHOUT MEMORY ---")
            print(answer_without_memory(llm, step["message"]), "\n")

        print("--- WITH HINDSIGHT MEMORY ---")
        print(answer_with_memory(llm, memory, PROJECT_ID, step["message"]))

        # The agent remembers what just happened for the next interaction.
        memory.retain_note(PROJECT_ID, step["outcome_note"])
        time.sleep(PROCESSING_WAIT_SECONDS)

    memory.close()


if __name__ == "__main__":
    main()
