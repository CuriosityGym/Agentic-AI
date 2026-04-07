"""
langflow_client.py
──────────────────
The ONLY place this app talks to Langflow (or any LLM backend).

If you want to swap Langflow for a different AI backend
(e.g. OpenAI API, a local Ollama server, etc.) replace call_langflow()
here — nothing else in the codebase needs to change.
"""

import requests
from config import LANGFLOW_BASE_URL, FLOW_ID, HEADERS, get_api_key, TWEAKS_API_GOOGLE_COMPONENT_ID



def call_langflow(prompt: str, session_id: str) -> str:
    """
        Send a prompt to the Langflow flow and return the LLM's text response.

        Parameters
        ----------
        prompt     : the full text to send to the LLM
        session_id : unique per-browser-session ID so Langflow keeps conversations separate

        Returns
        -------
        The assistant's reply as a plain string.
    """
    gradio_api_key = get_api_key()
    if not gradio_api_key:
        print("⚠️ Codespace not Registered!")
        return "⚠️ Session token unavailable or expired. Please register this codespace."
    
    updated_headers = HEADERS.copy()
    updated_headers["gradio-token"] = gradio_api_key

    url = f"{LANGFLOW_BASE_URL}/api/v1/proxy/langflow/run/{FLOW_ID}"
    payload = {
        "input_value": prompt,
        "input_type":  "chat",
        "output_type": "chat",
        "session_id":  session_id,
        # Tweaks entry
        # Array to allow for multiple tweaks if needed in the future
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
        resp = requests.post(url, headers=updated_headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return (
            data.get("outputs", [{}])[0]
                .get("outputs", [{}])[0]
                .get("results", {})
                .get("message", {})
                .get("text", "No response from Langflow.")
        )
    except requests.exceptions.ConnectionError:
        return (
            "⚠️ Could not connect to Langflow. "
            "Make sure it is running at: " + LANGFLOW_BASE_URL
        )
    except Exception as e:
        return f"⚠️ Langflow API error: {e}"