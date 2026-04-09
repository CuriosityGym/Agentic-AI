"""
langflow_client.py — Sends messages to a Langflow flow and returns the AI reply.

What this file does:
    Provides a single function, call_langflow(), that wraps the Langflow
    REST API. Every interaction with the AI goes through this one function.

Students: You do NOT need to edit this file.
          To change what the AI says or how it behaves, update the
          system prompt in your Langflow flow (the Prompt Template node).
"""

import requests

from config import LANGFLOW_BASE_URL, LANGFLOW_FLOW_ID, LANGFLOW_API_KEY, HEADERS, get_api_key, TWEAKS_API_GOOGLE_COMPONENT_ID


def call_langflow(user_message: str, session_id: str, transcript: str = "") -> str:
    """
    Send a message to the Langflow flow and return the AI's reply.

    Args:
        user_message: The text message from the user.
        session_id:   A unique ID for this conversation. Langflow uses this
                      to remember the conversation history between messages.
        transcript:   (Optional) Full video transcript. Only needed on the
                      very first message for a new video URL.

    Returns:
        The AI's reply as a plain string.

    Raises:
        EnvironmentError: If LANGFLOW_FLOW_ID is not set in .env.
        ValueError:       If Langflow returns an auth or server error.
    """
    gradio_api_key = get_api_key()
    if not gradio_api_key:
        print("⚠️ Codespace not Registered!")
        return "⚠️ Session token unavailable or expired. Please register this codespace."


    if not LANGFLOW_FLOW_ID:
        raise EnvironmentError("LANGFLOW_FLOW_ID is not set. Add it to your .env file.")

    # On the first message for a new video, inject the full transcript so the
    # AI has content to summarise. Follow-up messages use Langflow's memory.
    if transcript:
        input_text = (
            "[VIDEO TRANSCRIPT]\n"
            f"{transcript}\n\n"
            "[USER MESSAGE]\n"
            f"{user_message}"
        )
    else:
        input_text = user_message

    # headers = {"Content-Type": "application/json"}
    # if LANGFLOW_API_KEY:
    #     headers["x-api-key"] = LANGFLOW_API_KEY
    headers = HEADERS.copy()
    headers["gradio-token"] = gradio_api_key

    payload = {
        "input_value": input_text,
        "output_type": "chat",
        "input_type": "chat",
        "session_id": session_id,
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

    resp = requests.post(
        f"{LANGFLOW_BASE_URL}/api/v1/proxy/langflow/run/{LANGFLOW_FLOW_ID}",
        headers=headers,
        json=payload,
        timeout=90,
    )

    if resp.status_code == 401:
        raise ValueError("Langflow auth failed. Check LANGFLOW_API_KEY in .env.")
    if resp.status_code != 200:
        raise ValueError(f"Langflow error {resp.status_code}: {resp.text[:400]}")

    data = resp.json()

    # Standard Langflow response path
    try:
        return data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
    except (KeyError, IndexError, TypeError):
        pass

    # Fallback: search any output block for a non-empty text field
    for outer in data.get("outputs", []):
        for inner in outer.get("outputs", []):
            msg = inner.get("results", {}).get("message", {})
            text = msg.get("text") or msg.get("content")
            if text:
                return text

    return f"Could not parse Langflow response. Raw: {str(data)[:500]}"