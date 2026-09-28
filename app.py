"""
Scope Creep Detector: Streamlit UI.

Your project has a memory. The agent remembers what you agreed to and what
happened later. Hindsight is the memory; Streamlit session state only tracks
which project is open.

Flow:

1. Pick the Brightleaf demo project, or create your own (paste any agreement).
2. The agreement is retained in a fresh, isolated Hindsight bank.
3. Paste ANY client request -> Hindsight recall -> Groq analysis -> verdict.
4. The request and decision are retained, so the next request can recall them.

Run:

    streamlit run app.py
"""

import os
import uuid
import time

import streamlit as st
from dotenv import load_dotenv

from scope_creep_agent.agent import (
    analyze_with_memory,
    answer_without_memory,
    retain_interaction,
)

from scope_creep_agent.data import (
    DEMO_CLIENT_NAME,
    DEMO_PROJECT_NAME,
    ORIGINAL_SCOPE,
    TIMELINE,
)

from scope_creep_agent.llm import LLM
from scope_creep_agent.memory import ProjectMemory


load_dotenv()


# Hindsight extracts facts from retained text in the background, so we wait
# briefly before recalling something we just retained.
WAIT = int(os.environ.get("PROCESSING_WAIT_SECONDS", "8"))


STATUS_LABELS = {
    "NONE": "None",
    "PROPOSED": "Proposed, awaiting client approval",
    "APPROVED": "Approved by client",
    "REJECTED": "Rejected by client",
}


st.set_page_config(
    page_title="Scope Creep Detector",
    page_icon="🧠",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Simple UI styling
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
        .main {
            padding-top: 2rem;
        }

        h1 {
            font-size: 3rem !important;
            margin-bottom: 0.2rem !important;
        }

        .subtitle {
            color: #9ca3af;
            font-size: 1.05rem;
            margin-bottom: 2rem;
        }

        .section-card {
            padding: 1.4rem;
            border: 1px solid #30323a;
            border-radius: 14px;
            background: #111318;
            margin-bottom: 1rem;
        }

        .badge {
            display: inline-block;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: #252733;
            color: #d1d5db;
            font-size: 0.8rem;
            margin-bottom: 0.8rem;
        }

        div.stButton > button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.55rem 1rem;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            border-radius: 9px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

@st.cache_resource
def get_llm():
    return LLM() 


llm=get_llm()
memory = ProjectMemory()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def start_project(name: str, client: str, agreement: str, is_demo: bool) -> None:
    """Create a fresh Hindsight bank for this project and retain the agreement."""

    with st.spinner(
        "Creating project memory: retaining the agreement in Hindsight..."
    ):
        project_id = (
            f"{name.strip().lower().replace(' ', '-')}-"
            f"{uuid.uuid4().hex[:8]}"
        )

        memory.retain_scope(project_id, agreement)

        time.sleep(WAIT)

    st.session_state.project = {
        "name": name,
        "client": client,
        "agreement": agreement,
        "project_id": project_id,
        "bank_id": memory.bank_id(project_id),
        "is_demo": is_demo,
    }

    st.session_state.results = []
    st.session_state.history = []


def reset_project() -> None:
    for key in ("project", "results", "history"):
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Scope Creep Detector")

st.markdown(
    '<div class="subtitle">'
    "Your project has a memory. Track what was agreed, catch scope creep, "
    "and keep client decisions connected."
    "</div>",
    unsafe_allow_html=True,
)


project = st.session_state.get("project")


# ---------------------------------------------------------------------------
# 1. Choose / create project
# ---------------------------------------------------------------------------

if project is None:

    demo_col, custom_col = st.columns([1, 1.6], gap="large")

    # -----------------------------------------------------------------------
    # Demo project
    # -----------------------------------------------------------------------

    with demo_col:

        st.subheader("Demo project")

        st.write(
            "Try it instantly with a sample freelance project "
            f"(**{DEMO_PROJECT_NAME}**, {DEMO_CLIENT_NAME})."
        )

        with st.expander("See the demo agreement"):
            st.text(ORIGINAL_SCOPE.strip())

        if st.button("Use Demo Project", type="primary"):
            start_project(
                DEMO_PROJECT_NAME,
                DEMO_CLIENT_NAME,
                ORIGINAL_SCOPE,
                is_demo=True,
            )

            st.rerun()

    # -----------------------------------------------------------------------
    # Custom project
    # -----------------------------------------------------------------------

    with custom_col:

        st.subheader("Create custom project")

        with st.form("create_project"):

            name = st.text_input(
                "Project name",
                placeholder="Acme Website Redesign",
            )

            client = st.text_input(
                "Client name",
                placeholder="Acme Corp",
            )

            agreement = st.text_area(
                "Original agreement / project scope",
                height=240,
                placeholder=(
                    "Paste anything: kickoff notes, contract summary, "
                    "deliverables, exclusions, price, deadline, revision "
                    "limits, client decisions..."
                ),
            )

            created = st.form_submit_button(
                "Create Project Memory",
                type="primary",
            )

        if created:

            if not name.strip() or not agreement.strip():

                st.error(
                    "Project name and original agreement are required."
                )

            else:

                start_project(
                    name.strip(),
                    client.strip() or "Client",
                    agreement.strip(),
                    is_demo=False,
                )

                st.rerun()

    st.stop()


# ---------------------------------------------------------------------------
# 2. Project is active
# ---------------------------------------------------------------------------

left, right = st.columns([1, 1.8], gap="large")


# ---------------------------------------------------------------------------
# Project memory panel
# ---------------------------------------------------------------------------

with left:

    st.subheader("Project memory")

    st.markdown(f"**Project:** {project['name']}")

    st.markdown(f"**Client:** {project['client']}")

    with st.expander("Original agreement", expanded=False):
        st.text(project["agreement"])

    st.markdown(
        f"**Hindsight bank:** `{project['bank_id']}`"
    )

    st.success("Kickoff agreement retained in Hindsight")

    st.subheader("Project history")

    if st.session_state.history:

        for i, note in enumerate(
            st.session_state.history,
            1,
        ):
            st.markdown(f"**{i}.** {note}")

    else:

        st.caption(
            "Interactions retained in this session appear here."
        )

    with st.expander(
        "Everything Hindsight remembers (live recall)"
    ):

        if st.button("Recall project history"):

            with st.spinner("Asking Hindsight..."):

                everything = memory.recall_project_context(
                    project["project_id"],
                    "all client requests, decisions and the original agreement",
                )

            st.text(
                everything or "(nothing recalled yet)"
            )

    st.divider()

    if st.button("Reset / new project memory"):

        reset_project()

        st.rerun()


# ---------------------------------------------------------------------------
# Client message / analysis panel
# ---------------------------------------------------------------------------

with right:

    st.subheader("Client message")

    preset = None

    if project["is_demo"]:

        labels = ["Custom message"] + [
            t["label"]
            for t in TIMELINE
        ]

        choice = st.selectbox(
            "Load a demo message (or write your own)",
            labels,
        )

        preset = next(
            (
                t
                for t in TIMELINE
                if t["label"] == choice
            ),
            None,
        )

        msg_key = f"msg_{choice}"

    else:

        msg_key = "msg_custom"

    message = st.text_area(
        "Message",
        value=preset["message"] if preset else "",
        height=150,
        key=msg_key,
        placeholder=(
            "Can we also add a payment gateway to the website?"
        ),
    )

    compare = st.checkbox(
        "Also show the agent without memory",
        value=False,
    )

    if st.button(
        "Analyze Request",
        type="primary",
        disabled=not message.strip(),
    ):

        with st.spinner(
            "Recalling from Hindsight and reasoning with Groq..."
        ):

            baseline = (
                answer_without_memory(
                    llm,
                    message,
                )
                if compare
                else None
            )

            analysis = analyze_with_memory(
                llm,
                memory,
                project["project_id"],
                message,
            )

        with st.spinner(
            "Retaining this interaction in Hindsight..."
        ):

            note = retain_interaction(
                memory,
                project["project_id"],
                message,
                analysis,
            )

            time.sleep(WAIT)

        st.session_state.history.append(note)

        st.session_state.results.insert(
            0,
            {
                "message": message,
                "baseline": baseline,
                "analysis": analysis,
            },
        )

        st.rerun()


    # -----------------------------------------------------------------------
    # Results
    # -----------------------------------------------------------------------

    if not st.session_state.results:

        st.caption(
            "Results appear here after you analyze a request."
        )


    for res in st.session_state.results:

        a = res["analysis"]

        with st.container(border=True):

            st.markdown(
                f"**Client:** {res['message'][:200]}"
            )

            # ---------------------------------------------------------------
            # Verdict UI
            # ---------------------------------------------------------------

            if a.verdict == "OUT_OF_SCOPE":

                if a.change_order_status == "APPROVED":

                    st.warning(
                        "🟡 OUT OF ORIGINAL SCOPE — change order approved"
                    )

                elif a.change_order_status == "PROPOSED":

                    st.error(
                        "🔴 OUT OF SCOPE — change order needed"
                    )

                elif a.change_order_status == "REJECTED":

                    st.error(
                        "🔴 OUT OF SCOPE — change order rejected"
                    )

                else:

                    st.error(
                        "🔴 OUT OF SCOPE — change order needed"
                    )

            elif a.verdict == "IN_SCOPE":

                st.success("🟢 IN SCOPE")

            else:

                st.warning(
                    "UNKNOWN — no matching project memory found"
                )


            st.markdown(
                f"**Change order:** "
                f"{STATUS_LABELS.get(a.change_order_status, a.change_order_status)}"
            )


            if a.reason:

                st.markdown(
                    f"**Reasoning:** {a.reason}"
                )


            if a.recommended_action:

                st.markdown(
                    f"**Recommended action:** {a.recommended_action}"
                )


            if res["baseline"]:

                c1, c2 = st.columns(2)

                c1.markdown("**Without memory**")

                c1.write(
                    res["baseline"]
                )

                c2.markdown(
                    "**With Hindsight memory: agent response**"
                )

                c2.write(
                    a.reply
                )

            else:

                st.markdown(
                    "**Agent response**"
                )

                st.write(
                    a.reply
                )


            with st.expander(
                "Recalled from Hindsight",
                expanded=True,
            ):

                st.text(
                    a.recalled or "(nothing recalled)"
                )