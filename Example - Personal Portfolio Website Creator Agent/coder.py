import json
import logging

from config import CODER_FLOW_ID, CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID
from langflow_client import _run_flow, _extract_text_output, _parse_json_output
from designer import call_designer_agent

logger = logging.getLogger(__name__)


def call_coder_agent(student_data: dict, design: dict, session_id: str | None = None) -> dict:
    """Ask the AI to write the HTML, CSS, and JavaScript for the portfolio."""
    coder_input  = {"student_data": student_data, "design": design}
    raw_response = _run_flow(CODER_FLOW_ID, coder_input, session_id=session_id, tweaks=CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID)
    text_output  = _extract_text_output(raw_response)

    try:
        files = _parse_json_output(text_output)
    except json.JSONDecodeError:
        logger.warning("Coder agent output was not valid JSON; returning raw HTML fallback.")
        files = {
            "index.html": f"<html><body><pre>{text_output}</pre></body></html>",
            "style.css":  "",
            "main.js":    "",
        }

    _validate_website_files(files)
    return files


def _validate_website_files(files: dict) -> None:
    """Insert placeholder content for any missing output file."""
    defaults = {
        "index.html": "<html><body><h1>Portfolio</h1></body></html>",
        "style.css":  "/* Generated styles */",
        "main.js":    "// Generated scripts",
    }
    for key, placeholder in defaults.items():
        if key not in files or not isinstance(files[key], str):
            logger.warning("Coder agent output missing '%s'; using placeholder.", key)
            files[key] = placeholder


def run_portfolio_generation(student_data: dict, session_id: str | None = None) -> dict:
    """
    Run the full two-step AI pipeline:
      Step 1 – Designer Agent  → design specification
      Step 2 – Coder Agent     → website files (HTML / CSS / JS)
    """
    # Step 1: Get a design from the Designer Agent
    design = call_designer_agent(student_data, session_id=session_id)

    # Step 2: Generate website files (retry once if output is incomplete)
    for attempt in range(2):
        files    = call_coder_agent(student_data, design, session_id=session_id)
        required = {"index.html", "style.css", "main.js"}
        if required.issubset(files.keys()):
            break
        if attempt == 0:
            logger.warning("Coder output incomplete on attempt 1; retrying…")
        else:
            logger.error("Coder output still incomplete after retry; proceeding with what we have.")

    return files