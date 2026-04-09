import json
import logging
import re
from typing import Any

import requests

from config import LANGFLOW_BASE_URL, LANGFLOW_TOKEN, REQUEST_TIMEOUT, get_api_key

logger = logging.getLogger(__name__)


def _parse_json_output(text: str) -> dict | list:
    """Handle escaped/double-encoded JSON and markdown code fences."""
    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fence_match:
        text = fence_match.group(1)

    parsed = json.loads(text)

    if isinstance(parsed, str):
        parsed = json.loads(parsed)

    return parsed


def _build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if LANGFLOW_TOKEN:
        headers["x-api-key"] = LANGFLOW_TOKEN
    gradio_api_key = get_api_key()
    if not gradio_api_key:
        logger.warning("⚠️ Codespace not Registered!")
    else:
        headers["gradio-token"] = gradio_api_key
    logger.debug("Built headers for Langflow request: %s", headers)     
    return headers


def _run_flow(flow_id: str, input_value: Any, session_id: str | None, tweaks: str) -> dict:
    """Call a Langflow flow and return the parsed JSON response."""
    url = f"{LANGFLOW_BASE_URL}/api/v1/proxy/langflow/run/{flow_id}"

    if isinstance(input_value, (dict, list)):
        input_str = json.dumps(input_value)
    else:
        input_str = str(input_value)

    # payload = {"input_value": input_str}
    payload = {
        "input_value": input_str,
        "tweaks": [
            {
                "component_id": tweaks,
                "parameters": {
                    "type": "google_generative_ai",
                }
            }   
        ]
    }
    if session_id:
        payload["session_id"] = session_id

    try:
        response = requests.post(
            url,
            headers=_build_headers(),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as exc:
        logger.error("Langflow connection error for flow '%s': %s", flow_id, exc)
        raise RuntimeError("Could not connect to Langflow. Is it running on port 7860?") from exc
    except requests.exceptions.Timeout as exc:
        logger.error("Langflow request timed out for flow '%s'", flow_id)
        raise RuntimeError("Langflow request timed out. Please try again.") from exc
    except requests.exceptions.HTTPError as exc:
        logger.error(
            "Langflow HTTP error for flow '%s': %s – %s",
            flow_id, exc.response.status_code, exc.response.text,
        )
        raise RuntimeError(
            f"Langflow returned an error ({exc.response.status_code}). Please try again."
        ) from exc


def _extract_text_output(response: dict) -> str:
    """Extract the plain-text / JSON string from a Langflow API response."""
    try:
        return response["outputs"][0]["outputs"][0]["results"]["message"]["text"]
    except (KeyError, IndexError, TypeError):
        pass

    if "output" in response:
        return str(response["output"])

    return json.dumps(response)