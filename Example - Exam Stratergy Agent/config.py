"""
    config.py
    ─────────
    All configuration lives here.
    Change connection details once, here, instead of hunting through the codebase.
"""

import os
import threading
import time

# ─── Langflow connection ───────────────────────────────────────────────────────
LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "https://api.mysphere.net") # Do not change this URL
# Create Langflow API Key by going to settings -> API Keys -> New. Copy the API key and paste here. Same API key can be used for all flows within the same Langflow instance running inside your github Codespace. 
LANGFLOW_API_KEY  = os.getenv("LANGFLOW_API_KEY",  "")
FLOW_ID           = os.getenv("LANGFLOW_FLOW_ID",  "")
# You can fin the component ID for the Google Gemini API in your Langflow flow's URL when you select that component. It looks like "component-123abc". Copy that ID and set it here so the Langflow call can target it with the right tweaks.
TWEAKS_API_GOOGLE_COMPONENT_ID = os.getenv("TWEAKS_API_GOOGLE_COMPONENT_ID", "")

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": LANGFLOW_API_KEY,
}

# ─── Session state schema (for reference) ─────────────────────────────────────
# Every browser session keeps one state dict stored in gr.State.
#
# Key               Type    Description
# ─────────────────────────────────────────────────────────────────────────────
# session_id        str     unique ID sent to Langflow to keep sessions separate
# stage             str     controls which handler runs next (see router.py)
#                           values: "awaiting_pdf" | "awaiting_start" |
#                                   "in_test" | "scoring" | "reviewed"
# pdf_text          str     full extracted text of the uploaded PDF
# answer_key        dict    { "1": "A", "2": "C", ... }  from the PDF
# total_questions   int     total number of questions found in the PDF
# questions_order   list    shuffled list of question-number strings
# current_q_index   int     how many questions have been answered so far
# user_answers      dict    { "1": "A", "3": "C", ... } collected one-by-one

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