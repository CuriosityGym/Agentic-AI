"""Langflow REST API caller. Single source of truth for all Langflow calls."""
import json
import requests
from config import LANGFLOW_BASE_URL, LANGFLOW_FLOW_ID, LANGFLOW_API_KEY, get_api_key, TWEAKS_API_GOOGLE_COMPONENT_ID

_TIMEOUT = (10, 120)  # (connect, read)

def _get_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if LANGFLOW_API_KEY:
        headers["x-api-key"] = LANGFLOW_API_KEY
        gradio_api_key = get_api_key()
        if not gradio_api_key:
            print("⚠️ Codespace not Registered!")
            return "⚠️ Session token unavailable or expired. Please register this codespace."
        headers["gradio-token"] = gradio_api_key
    return headers

def is_langflow_available() -> bool:
    """Return True if the Langflow server is reachable."""
    try:
        resp = requests.get(f"{LANGFLOW_BASE_URL}/health", timeout=5, headers=_get_headers())
        return resp.status_code == 200
    except requests.RequestException:
        return False

def run_langflow_planner(payload: dict, session_id: str = "") -> dict:
    """Send a scheduling request to the configured Langflow flow.
    
    Returns dict with keys: scheduled, unscheduled
    Raises RuntimeError if the request fails or the response can't be parsed.
    """
    if not LANGFLOW_FLOW_ID:
        raise ValueError("LANGFLOW_FLOW_ID is not set in config.py")

    endpoint = f"{LANGFLOW_BASE_URL}/api/v1/proxy/langflow/run/{LANGFLOW_FLOW_ID}"
    body = {
        "input_value": json.dumps(payload),
        "input_type": "chat",
        "output_type": "chat",
        "session_id": session_id,
        # "tweaks": {},
        "tweaks": [
            {
                "component_id": TWEAKS_API_GOOGLE_COMPONENT_ID,
                "parameters": {
                    "type": "google_generative_ai",
                }
            }
        ]
    }

    try:
        resp = requests.post(endpoint, json=body, headers=_get_headers(), timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Langflow request failed: {exc}") from exc

    try:
        data = resp.json()
        output_text = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
        stripped = output_text.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[-1]
            stripped = stripped.rsplit("```", 1)[0]
        return json.loads(stripped.strip())
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unexpected Langflow response format: {exc}") from exc