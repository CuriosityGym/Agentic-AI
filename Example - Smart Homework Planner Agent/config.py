import os
import time
import threading

# ── App ───────────────────────────────────────────────────────────────────────
APP_TITLE = "Smart Homework Planner"

# ── Scheduler Defaults ────────────────────────────────────────────────────────
WORK_START_HOUR = 7      # Study sessions start at 7:00 AM
WORK_END_HOUR   = 21     # Study sessions end at 9:00 PM
MIN_SLOT_MINUTES = 15    # Ignore free slots shorter than this

# ── Langflow Connection ───────────────────────────────────────────────────────
LANGFLOW_BASE_URL = os.getenv("LANGFLOW_URL",     "https://api.mysphere.net") # Do not change this URL 
LANGFLOW_FLOW_ID  = os.getenv("LANGFLOW_FLOW_ID", "")
# Create Langflow API Key by going to settings -> API Keys -> New. Copy the API key and paste here. Same API key can be used for all flows within the same Langflow instance running inside your github Codespace.
LANGFLOW_API_KEY  = os.getenv("LANGFLOW_API_KEY",  "")
# You can find the component ID for the Google Generative AI in your Langflow flow when you select this component. A small box will appear that will display the ID. Over hove this ID. Click when it says "Click to Copy Full ID". After click the ID can be pasted below. ID looks like "component-123abc". Copy that ID and set it here so the Langflow call can target it with the right tweaks.
TWEAKS_API_GOOGLE_COMPONENT_ID = os.getenv("TWEAKS_API_GOOGLE_COMPONENT_ID", "")

# ── STRETCH ADDON CONFIG (uncomment when adding stretch features) ─────────────
# OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
# VECTOR_STORE_PATH  = os.getenv("VECTOR_STORE_PATH", "./vector_store")

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