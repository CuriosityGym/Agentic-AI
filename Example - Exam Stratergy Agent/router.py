"""
router.py
─────────
Message router. Every user message passes through chat() here.

How to add a new feature in 3 steps
─────────────────────────────────────
  1. Write a handler function in the appropriate feature file.
     Signature must be: handler(message: dict, state: dict) -> tuple[str, dict]

  2. Import it at the top of this file.

  3. Add one line to STAGE_HANDLERS:
         "your_stage_name": your_handler_function

  That's it. Also add one line to STAGE_STATUS_LABELS for the status bar text.
"""

import re
import uuid

from pdf_handler      import handle_pdf_upload
from test_engine      import handle_start_test, handle_in_test
from followup_handler import handle_general_question

# STRETCH 2.A — Explain Correct Answer
# Step 1: Uncomment the import below.
# Step 2: Find the STAGE_HANDLERS dict below and follow the comment there.
# from followup_handler import handle_explain_answer

# STRETCH 2.B — Generate Practice Questions
# Step 1: Uncomment the import below.
# Step 2: Find the STAGE_HANDLERS dict below and follow the comment there.
# from followup_handler import handle_generate_questions


# ─── Status bar labels ────────────────────────────────────────────────────────
# Text shown in the UI status bar at the bottom of the page.
# Add one entry here whenever you add a new stage.

STAGE_STATUS_LABELS: dict[str, str] = {
    "awaiting_pdf":   "⏳ Waiting for PDF upload...",
    "processing":     "🔄 Processing PDF...",
    "awaiting_start": "✅ PDF loaded — type **start** when ready!",
    "in_test":        "🎯 In test",          # ui.py appends the question count
    "scoring":        "🔄 Scoring...",
    "reviewed":       "🏁 Review complete — ask follow-up questions anytime!",
}


# ─── Per-stage handler functions ──────────────────────────────────────────────

def handle_awaiting_pdf(message: dict, state: dict) -> tuple[str, dict]:
    """No PDF yet — show the welcome message."""
    reply = (
        "👋 Welcome! Please attach your **PDF exam paper** using the 📎 button below. "
        "You can type a message along with it too."
    )
    return reply, state


def handle_awaiting_start(message: dict, state: dict) -> tuple[str, dict]:
    """
    PDF is loaded. Waiting for the student to say "start".
    Any other text is treated as a general question about the exam.
    """
    text = message.get("text", "").strip()
    if re.search(r'\bstart\b', text, re.IGNORECASE):
        return handle_start_test(state)
    return handle_general_question(message, state)


# ─── Stage → handler registry ─────────────────────────────────────────────────
# Maps each stage name to the function that should handle messages in that stage.
# To add a feature: write its handler → import it above → add one line here.

STAGE_HANDLERS: dict = {
    "awaiting_pdf":   handle_awaiting_pdf,
    "awaiting_start": handle_awaiting_start,
    "in_test":        handle_in_test,
    "reviewed":       handle_general_question, # This will be commented out whenever STRETCH 2.A or 2.B is activated, since both have their own handler functions.

    # ── STRETCH 2.A — Explain Correct Answer ──────────────────────────────────
    # handle_explain_answer detects "explain why option X is correct for question N"
    # and gives a richer answer than handle_general_question. For all other text
    # it falls back to handle_general_question, so nothing breaks.
    #
    # To activate:
    #   - Uncomment the import at the top of this file
    #   - Replace the "reviewed" line above with the line below:
    # "reviewed": handle_explain_answer,

    # ── STRETCH 2.B — Generate Practice Questions ──────────────────────────────
    # handle_generate_questions detects "generate N questions on <topic>".
    # For all other text it falls back to handle_general_question.
    #
    # To activate:
    #   - Uncomment the import at the top of this file
    #   - Replace the "reviewed" line above with the line below:
    # "reviewed": handle_generate_questions,

    # ── STRETCH 2.A + 2.B both active at the same time ────────────────────────
    # Each handler falls back to handle_general_question when its pattern doesn't
    # match. To chain them so BOTH patterns work, open followup_handler.py and
    # change the fallback inside handle_explain_answer from:
    #     return handle_general_question(message, state)
    # to:
    #     return handle_generate_questions(message, state)
    # Then register: "reviewed": handle_explain_answer
}


# ─── Initial state factory ─────────────────────────────────────────────────────

def make_initial_state() -> dict:
    """Return a clean, empty session state dict for a new browser session."""
    return {
        "session_id":      str(uuid.uuid4()),
        "stage":           "awaiting_pdf",
        "pdf_text":        "",
        "answer_key":      {},
        "total_questions": 0,
        "questions_order": [],
        "current_q_index": 0,
        "user_answers":    {},
    }


# ─── Main router ───────────────────────────────────────────────────────────────

def chat(message: dict, history: list, state: dict) -> tuple[str, dict]:
    """
    Entry point called by Gradio on every submitted message.

    message  : { "text": str, "files": [path, ...] }
    history  : full chat history list (not used for routing)
    state    : mutable session state dict stored in gr.State
    """
    if not state.get("session_id"):
        state = make_initial_state()

    files = message.get("files", [])
    stage = state.get("stage", "awaiting_pdf")

    # A PDF file attachment always triggers the upload handler regardless of
    # the current stage — this lets the student re-upload mid-session.
    if files:
        return handle_pdf_upload(message, state)

    handler = STAGE_HANDLERS.get(stage, handle_general_question)
    return handler(message, state)