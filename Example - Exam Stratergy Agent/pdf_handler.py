"""
    pdf_handler.py
    ──────────────
    Feature: PDF Upload & Analysis
    ───────────────────────────────
    Everything needed for Step 1 of the app:
    - parse_pdf_fully()    extracts raw text from the uploaded PDF
    - handle_pdf_upload()  sends that text to Langflow to get the answer key,
                            topic list, and summary; then transitions to "awaiting_start"

    To REMOVE this feature: comment out its import line in router.py.
"""

import json
import re
import pdfplumber

from langflow_client import call_langflow


# ─── PDF text extractor ────────────────────────────────────────────────────────

def parse_pdf_fully(pdf_path: str) -> str:
    """Extract all pages from a PDF file using pdfplumber."""
    all_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    all_text += f"\n--- Page {i+1} of {total} ---\n{text}"
        if not all_text.strip():
            return "[PDF has no extractable text — may be scanned/image-based.]"
    except Exception as e:
        return f"[Error reading PDF: {e}]"
    return all_text


# ─── Stage handler ─────────────────────────────────────────────────────────────

def handle_pdf_upload(message: dict, state: dict) -> tuple[str, dict]:
    """
        Called whenever the user attaches a PDF.
        Parses the PDF, asks Langflow to extract the answer key and metadata,
        and transitions the session to the "awaiting_start" stage.
    """
    files     = message.get("files", [])
    user_text = message.get("text", "").strip()

    if not files:
        return "📎 Please attach a PDF exam paper to get started.", state

    pdf_path = files[0]
    pdf_text = parse_pdf_fully(pdf_path)

    state["pdf_text"] = pdf_text
    state["stage"]    = "processing"

    extraction_prompt = f"""
        You are an exam analysis assistant. Below is the full text of an exam paper.

        Your tasks:
        1. Count all the questions (just their numbers).
        2. For each question, find the answer denoted by "Answer: <option>" at the end
        of the question. Build an Answer Key as a JSON object like: {{"1":"A","2":"C",...}}
        3. If there is NO answer key at all, output: "NO_ANSWER_KEY"
        4. Do NOT reveal the answers to the user.
        5. Identify the topic types / subject areas covered.

        Respond in EXACTLY this format (no extra lines between fields):
        TOTAL_QUESTIONS: <number>
        ANSWER_KEY: <JSON object OR "NO_ANSWER_KEY">
        TOPICS: <comma-separated list of topic/subject areas>
        SUMMARY: <one sentence about the exam>

        --- EXAM PAPER ---
        {pdf_text[:12000]}
        {"...[truncated]..." if len(pdf_text) > 12000 else ""}
    """

    intro = user_text if user_text else "Please analyze this exam paper."
    lf_response = call_langflow(f"{intro}\n\n{extraction_prompt}", state["session_id"])

    # ── Second AI call: extract all questions + options + answers ──────────────
    questions_prompt = f"""
        You are an exam paper parser. Below is the full text of an exam paper.

        Extract EVERY question from the paper. For each question return:
        - The question number (as a string, e.g. "1", "2")
        - The full question text
        - All four answer options (A, B, C, D)
        - The correct answer letter

        Respond with ONLY a JSON array — no explanation, no preamble, no trailing text.
        Use EXACTLY this schema:

        ```json
        [
        {{
            "number": "1",
            "text": "<full question text>",
            "options": {{
            "A": "<option A text>",
            "B": "<option B text>",
            "C": "<option C text>",
            "D": "<option D text>"
            }},
            "answer": "A"
        }}
        ]
        ```

        --- EXAM PAPER ---
        {pdf_text[:12000]}
        {"...[truncated]..." if len(pdf_text) > 12000 else ""}
    """

    questions_bank = []
    raw_q_response = call_langflow(questions_prompt, state["session_id"] + "_qbank")

    # Strip ```json ... ``` or ``` ... ``` fencing
    stripped = re.sub(r'^```(?:json)?\s*', '', raw_q_response.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r'\s*```$', '', stripped.strip())

    try:
        questions_bank = json.loads(stripped)
        if not isinstance(questions_bank, list):
            questions_bank = []
    except (json.JSONDecodeError, ValueError):
        questions_bank = []

    # ── Parse the structured LLM response ─────────────────────────────────────
    total_q    = 0
    answer_key = {}
    summary    = ""
    topics     = ""

    for line in lf_response.splitlines():
        line = line.strip()
        if line.startswith("TOTAL_QUESTIONS:"):
            try:
                total_q = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("ANSWER_KEY:"):
            raw = line.split(":", 1)[1].strip()
            if raw != "NO_ANSWER_KEY":
                try:
                    answer_key = json.loads(raw)
                except json.JSONDecodeError:
                    match = re.search(r'\{.*\}', raw)
                    if match:
                        try:
                            answer_key = json.loads(match.group())
                        except Exception:
                            pass
        elif line.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
        elif line.startswith("TOPICS:"):
            topics = line.split(":", 1)[1].strip()

    # ── Update session state ───────────────────────────────────────────────────
    state["answer_key"]      = answer_key
    state["total_questions"] = total_q
    state["stage"]           = "awaiting_start"
    state["user_answers"]    = {}
    state["questions_order"] = []
    state["current_q_index"] = 0
    state["questions_bank"] = questions_bank 

    has_key_msg = (
        f"✅ Answer key detected ({len(answer_key)} questions)."
        if answer_key else
        "⚠️ No answer key found in the PDF. Scoring will not be available."
    )

    reply = (
        f"📄 **PDF processed successfully!**\n\n"
        f"📝 **Summary:** {summary or 'Exam paper loaded.'}\n"
        f"🔢 **Total Questions:** {total_q or 'Detected (see paper)'}\n"
        f"📚 **Topics Covered:** {topics or 'See paper'}\n"
        f"{has_key_msg}\n\n"
        f"---\n"
        f"🚀 **Ready to start the test?**\n"
        f"Questions will be presented **one at a time in random order**.\n"
        f"Type **`start`** or **`start test`** when you're ready!"
    )
    return reply, state