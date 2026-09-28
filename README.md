# Scope Creep Detector

An AI agent that remembers what was actually agreed with a client — so it can
catch new requests that quietly fall outside the original scope, using
[Hindsight](https://hindsight.vectorize.io/) as its memory layer.

## The problem

Freelancers and agencies lose money to scope creep not because clients are
bad actors, but because nobody re-reads the original brief three weeks in.
"Can you also just add a login page?" sounds small in isolation. It's only
scope creep when you remember what was originally agreed.

## How it works

1. **Retain** — when a project kicks off, the original scope (deliverables,
   what's explicitly excluded, the quote) is stored in a dedicated Hindsight
   memory bank for that project.
2. A client sends a new message during the project (a Slack message, an
   email, a call transcript — anything).
3. **Recall** — before answering, the agent recalls the original scope
   memories relevant to the new request.
4. The LLM (via Groq) compares the new request against what was recalled and
   decides: in-scope, or flag it, with a specific reference to what was
   originally agreed.

Without memory, an agent can only respond to the message in front of it. With
Hindsight, it can compare that message against a scope agreement from weeks
ago — that comparison is the entire product.

## Project structure

```
scope_creep_agent/
  llm.py       # Groq client wrapper (LLM calls)
  memory.py     # Hindsight client wrapper (retain / recall)
  data.py       # Synthetic project scope + client message timeline (demo data)
  agent.py      # Core logic: analyze a client message with/without memory
demo.py         # Runs the before/after comparison end-to-end
requirements.txt
.env.example
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your real keys
```

You need:
- A Hindsight Cloud instance + API key (`ui.hindsight.vectorize.io` — use
  promo code `MEMHACK99` for $50 free credit, added in the billing section
  *after* signup)
- A Groq API key (`groq.com` — free tier)

## Run the demo

```bash
python demo.py
```

This retains a sample project scope, then sends the same "new request" from
a client through the agent twice:

- **Without memory** — generic, says yes to everything
- **With memory (Hindsight recall)** — catches that the request falls
  outside the agreed scope and explains exactly why, citing the original
  agreement

That before/after contrast is the core demo.

## Notes / limitations

- This is a CLI demo, not a production integration (no real Slack/email
  ingestion yet — client messages are simulated in `data.py`).
- Scope comparison quality depends on how much detail was retained at
  kickoff; a one-line scope note will recall poorly compared to a structured
  one.
