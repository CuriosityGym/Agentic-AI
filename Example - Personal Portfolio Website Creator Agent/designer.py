import json
import logging

from config import DESIGNER_FLOW_ID, DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID
from langflow_client import _run_flow, _extract_text_output, _parse_json_output

logger = logging.getLogger(__name__)


def call_designer_agent(student_data: dict, session_id: str | None = None) -> dict:
    """Ask the AI to design the website layout and theme."""
    raw_response = _run_flow(DESIGNER_FLOW_ID, student_data, session_id=session_id, tweaks=DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID)
    text_output  = _extract_text_output(raw_response)

    try:
        design = _parse_json_output(text_output)
    except json.JSONDecodeError:
        logger.warning("Designer agent output was not valid JSON; using defaults.")
        design = {
            "theme":    "light",
            "layout":   "standard",
            "sections": ["about", "projects", "skills", "contact"],
            "raw":      text_output,
        }

    return design