"""
config.py — All configuration for the YouTube Summarizer app.

Students: Do NOT put real API keys directly in this file.
          Instead, create a file named .env in this folder and add:

              SUPDATA_API_KEY=your_key_here
              LANGFLOW_BASE_URL=http://127.0.0.1:7860
              LANGFLOW_FLOW_ID=your_flow_id_here
              LANGFLOW_API_KEY=your_langflow_key_here

          The app loads those values automatically at startup.
"""

import os
from dotenv import load_dotenv
import threading
import time

load_dotenv()

LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "https://api.mysphere.net") # Do not change this URL
LANGFLOW_FLOW_ID  = os.getenv("LANGFLOW_FLOW_ID",  "")
# Create Langflow API Key by going to settings -> API Keys -> New. Copy the API key and paste here. Same API key can be used for all flows within the same Langflow instance running inside your github Codespace.
LANGFLOW_API_KEY  = os.getenv("LANGFLOW_API_KEY",  "")
# You can find the component ID for the Google Generative AI in your Langflow flow when you select this component. A small box will appear that will display the ID. Over hove this ID. Click when it says "Click to Copy Full ID". After click the ID can be pasted below. ID looks like "component-123abc". Copy that ID and set it here so the Langflow call can target it with the right tweaks.
TWEAKS_API_GOOGLE_COMPONENT_ID = os.getenv("TWEAKS_API_GOOGLE_COMPONENT_ID", "")
TRANSCRIPT_URL = f"{LANGFLOW_BASE_URL}/api/v1/proxy/supadata/transcript"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": LANGFLOW_API_KEY,
}

# Runtime token store — written by inject_token API, read by langflow_client
_api_key_store: dict = {}
_store_lock = threading.Lock()

def set_api_key(jwt_token: str) -> str:
    """
    Called by @gradio/client from your Node.js backend after JWT mint.
    
    Google Gemini API key is never shored to Gradio. Instead, we store the raw JWT token and only extract the API key at call time in NodeJS API, with expiry checks.

    Do not store the JWT token anywhere in Gradio. If user refreshes the page, they will need to mint a new token and call this API again, which is good for security.
    
    """
    try:
        api_key = jwt_token 
        if not api_key:
            return "error:invalid_token"
        with _store_lock:
            _api_key_store["active"] = {
                "key": api_key,
                "exp": time.time() + 7200
            }
        return "ok"
    except Exception as e:
        return f"error:invalid"

def get_api_key() -> str | None:
    """Called by langflow_client before every Langflow request."""
    with _store_lock:
        entry = _api_key_store.get("active")
    if not entry:
        return None
    # Guard against expired tokens (double-check at call time)
    if entry.get("exp") and time.time() > entry["exp"]:
        return None
    return entry["key"]