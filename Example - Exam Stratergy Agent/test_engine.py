"""
    test_engine.py
    ──────────────
    Feature: Scored Test (one question at a time)
    ──────────────────────────────────────────────
    The complete scored-test pipeline lives here:
    - parse_single_answer()  parses A/B/C/D from free-form user text
    - score_answers()        compares user answers against the answer key
    - fetch_question_text()  asks LLM to show one question without its answer
    - handle_start_test()    shuffles questions, sends the first one
    - handle_in_test()       records an answer, sends the next question
    - handle_end_test()      scores everything, asks LLM for full analysis

    To REMOVE this feature: comment out its import lines in router.py.
"""

import re
import json
import random

from langflow_client import call_langflow


# ─── Helpers ───────────────────────────────────────────────────────────────────

def parse_single_answer(text: str) -> str | None:
    """
    Parse a single answer option (A/B/C/D) from user input.
    Accepts: 'A', 'b', 'option A', 'my answer is C', etc.
    Returns an uppercase letter, or None if nothing matched.
    """
    match = re.search(r'\b([A-Da-d])\b', text)
    if match:
        return match.group(1).upper()
    return None


def score_answers(user_answers: dict, answer_key: dict) -> dict:
    """
    Compare user answers against the answer key.

    Returns a dict:
        correct     — count of correct answers
        wrong       — list of { q, user, correct } dicts
        unattempted — list of question numbers not answered
        total       — total number of questions in the key
        score_str   — human-readable "7/10" style string
    """
    total       = len(answer_key)
    correct     = 0
    wrong       = []
    unattempted = []

    for qnum, correct_ans in answer_key.items():
        user_ans = user_answers.get(qnum)
        if user_ans is None:
            unattempted.append(qnum)
        elif user_ans == correct_ans:
            correct += 1
        else:
            wrong.append({
                "q":       qnum,
                "user":    user_ans,
                "correct": correct_ans,
            })

    return {
        "correct":     correct,
        "wrong":       wrong,
        "unattempted": unattempted,
        "total":       total,
        "score_str":   f"{correct}/{total}",
    }

# Uses LLM to fetch next question which is slower and wastes tokens
# def fetch_question_text(q_number: str, pdf_text: str, session_id: str) -> str:
#     """
#     Ask the LLM to pull one question from the PDF and display it cleanly.
#     The correct answer must NOT appear in the response.
#     """
#     prompt = f"""
#         You are an exam assistant conducting a test.

#         From the exam paper below, extract ONLY Question {q_number} — including its full
#         question text and all answer options (A, B, C, D).
#         Do NOT include the answer or any hint about which option is correct.
#         Format it cleanly like:

#         **Question {q_number}**
#         <question text>

#         A) <option A>
#         B) <option B>
#         C) <option C>
#         D) <option D>

#         --- EXAM PAPER ---
#         {pdf_text[:12000]}
#     """
#     return call_langflow(prompt, session_id)

def fetch_question_text(q_number: str, state: dict) -> str:
    """
    Serve one question from the pre-built questions_bank.
    Falls back to an LLM call only if the bank is missing or incomplete.
    """
    bank: list = state.get("questions_bank", [])
    entry = next((q for q in bank if str(q.get("number")) == str(q_number)), None)

    if entry:
        opts = entry.get("options", {})
        return (
            f"**Question {q_number}**\n"
            f"{entry.get('text', '')}\n\n"
            f"A) {opts.get('A', '')}\n"
            f"B) {opts.get('B', '')}\n"
            f"C) {opts.get('C', '')}\n"
            f"D) {opts.get('D', '')}"
        )

    # Fallback: ask the LLM (old behaviour)
    prompt = f"""
        You are an exam assistant conducting a test.
        From the exam paper below, extract ONLY Question {q_number} — including its full
        question text and all answer options (A, B, C, D).
        Do NOT include the answer or any hint about which option is correct.
        Format it cleanly like:

        **Question {q_number}**
        <question text>

        A) <option A>
        B) <option B>
        C) <option C>
        D) <option D>

        --- EXAM PAPER ---
        {state['pdf_text'][:12000]}
    """
    return call_langflow(prompt, state["session_id"])


# ─── Stage handlers ────────────────────────────────────────────────────────────

def handle_start_test(state: dict) -> tuple[str, dict]:
    """
    Student said "start". Shuffle question order and send the first question.
    """
    answer_key = state.get("answer_key", {})
    if not answer_key:
        return (
            "⚠️ No answer key was found so I can't run the scored test. "
            "You can still ask me questions about the exam topics.",
            state,
        )

    q_numbers = list(answer_key.keys())
    random.shuffle(q_numbers)
    state["questions_order"] = q_numbers
    state["current_q_index"] = 0
    state["user_answers"]    = {}
    state["stage"]           = "in_test"

    total       = len(q_numbers)
    first_q_num = q_numbers[0]
    # q_text      = fetch_question_text(first_q_num, state["pdf_text"], state["session_id"])
    q_text = fetch_question_text(first_q_num, state)

    reply = (
        f"🎯 **Test started! {total} questions, presented randomly.**\n\n"
        f"_(Question 1 of {total})_\n\n"
        f"{q_text}\n\n"
        f"---\n_Reply with just the option letter: **A**, **B**, **C**, or **D**_"
    )
    return reply, state


def handle_in_test(message: dict, state: dict) -> tuple[str, dict]:
    """
    Test is in progress. Accept one answer, record it, then either send the
    next question or hand off to handle_end_test() when all are answered.
    """
    text          = message.get("text", "").strip()
    answer        = parse_single_answer(text)
    current_q_num = state["questions_order"][state["current_q_index"]]

    if answer is None:
        return (
            f"⚠️ I didn't catch a valid answer. "
            f"Please reply with **A**, **B**, **C**, or **D** for Question {current_q_num}.",
            state,
        )

    state["user_answers"][current_q_num] = answer
    state["current_q_index"] += 1

    total    = len(state["questions_order"])
    answered = state["current_q_index"]

    if answered >= total:
        state["stage"] = "scoring"
        return handle_end_test(state)

    next_q_num = state["questions_order"][answered]
    # q_text     = fetch_question_text(next_q_num, state["pdf_text"], state["session_id"])
    q_text = fetch_question_text(next_q_num, state)


    reply = (
        f"✅ Got it — you answered **{answer}** for Question {current_q_num}.\n\n"
        f"---\n\n"
        f"_(Question {answered + 1} of {total})_\n\n"
        f"{q_text}\n\n"
        f"---\n_Reply with just the option letter: **A**, **B**, **C**, or **D**_"
    )
    return reply, state


def handle_end_test(state: dict) -> tuple[str, dict]:
    """
    All questions answered. Calculate the score then ask Langflow for
    a detailed analysis: explanations for wrong answers, strategy, weak topics.
    """
    state["stage"] = "reviewed"
    result         = score_answers(state["user_answers"], state["answer_key"])

    wrong_details = "\n".join(
        f"  Q{w['q']}: You answered **{w['user']}**, correct is **{w['correct']}**"
        for w in result["wrong"]
    ) or "  None! Perfect score on attempted questions."

    unattempted_str = (
        f"  Questions: {', '.join(result['unattempted'])}"
        if result["unattempted"] else "  None — all attempted!"
    )

    eval_prompt = f"""
The student has just completed an exam (one question at a time, random order).
Here are the results:

Score: {result['score_str']} ({result['correct']} correct out of {result['total']} total)
Wrong answers: {json.dumps(result['wrong'])}
Unattempted: {result['unattempted']}

Full exam text (for context on wrong questions):
{state.get('pdf_text', '')[:8000]}

Please provide:
1. **Score Summary** - State the score clearly with percentage
2. **Explanation for Wrong Answers** - For each wrong question, explain the concept
   and why the correct answer is right
3. **Exam Strategy** - Specific tips to solve this type of paper more efficiently
4. **Weak Topics** - Highlight topic areas the student needs to focus on

Don't go beyond 1000 words for sections 2, 3, and 4 combined.

STRICT FORMATTING RULES — follow every rule below without exception:
- Every mathematical expression, number with a variable, formula, or symbol
  MUST be wrapped in LaTeX delimiters. No exceptions.
- Subscripts: $a_1$, $a_2$, $x_{{n-1}}$, $T_n$ — NEVER write a1 or x_n in plain text.
- Superscripts: $r^2$, $x^{{n-1}}$, $e^{{i\\pi}}$ — NEVER write r^2 in plain text.
- Inline expressions: single dollar signs — e.g. $a_n = a_1 \\cdot r^{{n-1}}$
- Standalone equations: double dollar signs — e.g. $$a_1 r^2 = \\sqrt{{28}}$$
- Fractions: $\\frac{{numerator}}{{denominator}}$
- Square roots: $\\sqrt{{x}}$
- Greek letters: $\\alpha$, $\\beta$, $\\theta$, $\\pi$, $\\Delta$
- Operators: $\\times$, $\\div$, $\\Rightarrow$, $\\leq$, $\\geq$, $\\neq$, $\\approx$
- NEVER write any math in plain text.

Be encouraging but honest. Format with clear Markdown headers.
"""

    lf_response = call_langflow(eval_prompt, state["session_id"])

    reply = (
        f"🏁 **Test complete! All questions answered.**\n\n"
        f"_Calculating your results..._\n\n"
        f"---\n\n"
        f"## 📊 Results\n\n"
        f"**Score: {result['score_str']}**\n\n"
        f"**Wrong Answers:**\n{wrong_details}\n\n"
        f"**Unattempted:**\n{unattempted_str}\n\n"
        f"---\n\n"
        f"{lf_response}\n\n"
        f"---\n_Feel free to ask any follow-up questions about the topics!_"
    )
    return reply, state