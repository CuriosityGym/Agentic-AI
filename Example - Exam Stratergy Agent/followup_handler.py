"""
followup_handler.py
───────────────────
Feature: Free Q&A
──────────────────
handle_general_question() is the catch-all handler. It answers any free-form
question the student types, using the exam PDF as context.

This file also contains COMMENTED-OUT scaffolding for two stretch exercises:

  STRETCH 2.A — Explain Correct Answer
      Student asks: "Explain why option A is correct for Question 5"
      To activate: uncomment the block below, then follow the steps in router.py

  STRETCH 2.B — Generate Practice Questions   ⚠️  Read the warning first
      Student asks: "Generate 3 more questions on Thermodynamics"
      To activate: uncomment the block below, then follow the steps in router.py
"""

import re
from langflow_client import call_langflow


# ─── Core handler (always active) ─────────────────────────────────────────────

def handle_general_question(message: dict, state: dict) -> tuple[str, dict]:
    """
    Handles any free-form text message from the student.
    Sends the first 4000 characters of the exam PDF as context so the LLM
    can answer questions about specific topics or questions in the paper.
    """
    text = message.get("text", "").strip()
    if not text:
        return "Please type your question.", state

    pdf_context = ""
    if state.get("pdf_text"):
        pdf_context = f"\n\nExam context (first 4000 chars):\n{state['pdf_text'][:4000]}"

    lf_response = call_langflow(text + pdf_context, state["session_id"])
    return lf_response, state


# ══════════════════════════════════════════════════════════════════════════════
# 🔧 STRETCH 2.A — Explain Correct Answer
# ══════════════════════════════════════════════════════════════════════════════
# Goal: After the test, the student can ask:
#   "Explain why option A is correct for Question 5"
# The handler detects this pattern, looks up the correct answer from the
# answer key already stored in state, and prompts Langflow for a detailed
# explanation with the wrong options also explained.
#
# How to activate (two steps):
#   Step 1: Uncomment the EXPLAIN_PATTERN constant and handle_explain_answer()
#           function below.
#   Step 2: Open router.py, find the "STRETCH 2.A" comment block, and follow
#           the instructions there to register this handler.
# ══════════════════════════════════════════════════════════════════════════════

# Patterns that will match or work in EXPLAIN_PATTERN
"""
    "explain why option B was chosen for question 3"
    "explain why option C is the answer to question 7"
    "can you explain why option D is right in question 1" (uses re.search, not re.match, so a sentence prefix is fine)
    "explain why option a is incorrect for question 2
"""
# EXPLAIN_PATTERN = re.compile(
#     r'explain\s+why\s+option\s+([A-Da-d])\s+.*?question\s+(\d+)',
#     re.IGNORECASE,
# )
# 
# def handle_explain_answer(message: dict, state: dict) -> tuple[str, dict]:
#     """
#     STRETCH 2.A: Handles "explain why option X is correct for question N".
#     Falls back to handle_general_question() if the pattern is not matched,
#     so all other free-form questions still work normally.
#     """
#     text  = message.get("text", "").strip()
#     match = EXPLAIN_PATTERN.search(text)

#     if not match:
#         # Not a structured explain request — fall through to general Q&A
#         return handle_general_question(message, state)

#     option  = match.group(1).upper()
#     q_num   = match.group(2)
#     correct = state.get("answer_key", {}).get(q_num)

#     if not correct:
#         return (
#             f"⚠️ I couldn't find Question {q_num} in the answer key. "
#             f"Try asking about it in a different way.",
#             state,
#         )

#     prompt = f"""
#         The student wants a detailed explanation for Question {q_num}.
#         The correct answer is option {correct}.

#         Using the exam paper below:
#         1. State clearly that option {correct} is the correct answer.
#         2. Explain the concept or calculation that leads to option {correct}.
#         3. Briefly explain why each of the other options is wrong.
#         4. Use LaTeX for ALL mathematical expressions (inline: $...$, block: $$...$$).

#         --- EXAM PAPER ---
#         {state.get('pdf_text', '')[:8000]}
#     """
#     reply = call_langflow(prompt, state["session_id"])
#     return reply, state


# ══════════════════════════════════════════════════════════════════════════════
# 🔧 STRETCH 2.B — Generate Practice Questions - Prone To Hallucinations
# ══════════════════════════════════════════════════════════════════════════════
# ⚠️  HALLUCINATION WARNING
#     LLMs can generate questions with subtly incorrect answer keys,
#     especially for math/science. A formula, number, or option may look
#     right but be wrong. ALWAYS have a teacher verify generated questions
#     before students use them for serious practice.
#     The reply labels all output as "AI-generated, unverified" to be clear.
#
# Goal: The student can ask:
#   "Generate 3 more questions on Thermodynamics"
# The LLM uses the uploaded PDF as a style and difficulty reference, then
# creates new questions with different wording but the same concept.
#
# How to activate (two steps):
#   Step 1: Uncomment the GENERATE_PATTERN constant and handle_generate_questions()
#           function below.
#   Step 2: Open router.py, find the "STRETCH 2.B" comment block, and follow
#           the instructions there to register this handler.
# ══════════════════════════════════════════════════════════════════════════════

# GENERATE_PATTERN = re.compile(
#     r'generate\s+(\d+)?\s*(?:more\s+)?questions?\s+(?:from|on|about)\s+(.+)',
#     re.IGNORECASE,
# )
#
# def handle_generate_questions(message: dict, state: dict) -> tuple[str, dict]:
#     """
#     STRETCH 2.B: Handles "generate N questions on <topic>".
#     Falls back to handle_general_question() if the pattern is not matched.
#     """
#     text  = message.get("text", "").strip()
#     match = GENERATE_PATTERN.search(text)
#
#     if not match:
#         return handle_general_question(message, state)
#
#     count = match.group(1) or "3"
#     topic = match.group(2).strip()
#
#     prompt = f"""
# Using the exam paper below as a style and difficulty guide, generate {count}
# new multiple-choice questions on the topic: "{topic}".
#
# Rules:
# - Match the difficulty level and format of the original questions.
# - Change the wording, numbers, or scenario but preserve the concept tested.
# - Provide 4 options (A, B, C, D) and an answer key for each question.
# - Use LaTeX for ALL mathematical expressions.
# - Begin your entire reply with this exact warning line (no exceptions):
#   ⚠️ AI-generated questions — answer key has NOT been verified by a teacher.
#
# --- EXAM PAPER (style reference) ---
# {state.get('pdf_text', '')[:8000]}
# """
#     reply = call_langflow(prompt, state["session_id"])
#     return reply, state