import os
import threading
import time

# ── Langflow Connection ────────────────────────────────────────────────────────
LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "https://api.mysphere.net") # Do not change this URL
# Create Langflow API Key / Langflow Token by going to settings -> API Keys -> New. Copy the API key and paste here. Same API key can be used for all flows within the same Langflow instance running inside your github Codespace
LANGFLOW_TOKEN    = os.getenv("LANGFLOW_TOKEN", "")
DESIGNER_FLOW_ID  = os.getenv("DESIGNER_FLOW_ID", "")
# You can find the component ID for the Google Generative AI in your Langflow flow when you select this component. A small box will appear that will display the ID. Over hove this ID. Click when it says "Click to Copy Full ID". After click the ID can be pasted below. ID looks like "component-123abc". Copy that ID and set it here so the Langflow call can target it with the right tweaks.
DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID = os.getenv("DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID", "")
CODER_FLOW_ID     = os.getenv("CODER_FLOW_ID", "")
# You can find the component ID for the Google Generative AI in your Langflow flow when you select this component. A small box will appear that will display the ID. Over hove this ID. Click when it says "Click to Copy Full ID". After click the ID can be pasted below. ID looks like "component-123abc". Copy that ID and set it here so the Langflow call can target it with the right tweaks.
CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID = os.getenv("CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID", "")
REQUEST_TIMEOUT   = 120  # seconds

# ── App Settings ───────────────────────────────────────────────────────────────
APP_HOST = "127.0.0.1"
APP_PORT = 7861

# ── Chat Step Constants ────────────────────────────────────────────────────────
STEP_NAME_SCHOOL_GRADE = 0
STEP_INTRODUCTION      = 1
STEP_LINKS             = 2
STEP_HOBBIES           = 3
STEP_INTERESTS         = 4
STEP_SKILLS            = 5
STEP_COURSES           = 6
STEP_PROJECTS          = 7
STEP_THEME             = 8
STEP_CONFIRM           = 9
STEP_DONE              = 10

# ── Step Prompts ───────────────────────────────────────────────────────────────
# Edit the text below to customise what the chatbot says at each step.
STEP_PROMPTS = {
    STEP_NAME_SCHOOL_GRADE: (
        "👋 Welcome to **Personal Portfolio Website Builder**!\n\n"
        "Let's start with the basics. Please tell me:\n\n"
        "- **Name:** Your full name\n"
        "- **School:** Your school or university\n"
        "- **Grade:** Your current grade / year\n\n"
        "You can type each on a separate line:\n"
        "```\nName: Alice Smith\nSchool: Riverside High\nGrade: 10\n```"
    ),
    STEP_INTRODUCTION: (
        "Great! Now write a short **introduction** about yourself.\n"
        "This will appear in the hero section of your portfolio.\n\n"
        "_Example: I'm a passionate student who loves coding and art._"
    ),
    STEP_LINKS: (
        "Share your **social / website links** (one per line).\n\n"
        "Format: `Platform: URL`\n\n"
        "```\nGithub: https://github.com/yourname\n"
        "LinkedIn: https://linkedin.com/in/yourname\n"
        "Instagram: https://instagram.com/yourname\n```\n\n"
        "_Type **skip** if you have none._"
    ),
    STEP_HOBBIES: (
        "What are your **hobbies**? (comma or newline separated)\n\n"
        "_Example: Reading, Coding, Hiking, Photography_\n\n"
        "_Type **skip** to leave this blank._"
    ),
    STEP_INTERESTS: (
        "What are your **interests / passions**? (comma or newline separated)\n\n"
        "_Example: Artificial Intelligence, Music Production, Space Exploration_\n\n"
        "_Type **skip** to leave this blank._"
    ),
    STEP_SKILLS: (
        "List your **technical or creative skills**. (comma or newline separated)\n\n"
        "_Example: Python, HTML, CSS, Graphic Design, Video Editing_\n\n"
        "_Type **skip** to leave this blank._"
    ),
    STEP_COURSES: (
        "Which **courses** have you taken or are currently enrolled in?\n"
        "(comma or newline separated)\n\n"
        "_Example: Computer Science, Mathematics, AP Physics, Web Development_\n\n"
        "_Type **skip** to leave this blank._"
    ),
    STEP_PROJECTS: (
        "Tell me about your **projects**! 🚀\n\n"
        "For each project type (one per line):\n"
        "```\nProject name | Short description\n```\n"
        "Example:\n"
        "```\nWeather App | A React app showing live weather forecasts\n"
        "Art Portfolio | Collection of my digital artworks\n```\n\n"
        "You can also **upload a file** (image, PDF, etc.) for any project using "
        "the upload button below.\n\n"
        "_Type **skip** to leave this blank._"
    ),
    STEP_THEME: (
        "Almost there! 🎨 Choose a **theme** for your portfolio website:\n\n"
        "- **dark** – sleek dark background\n"
        "- **light** – clean white background\n"
        "- **colorful** – vibrant gradient background\n"
        "- **minimal** – ultra-clean minimal look\n\n"
        "_Type your preference or press **skip** to let the AI decide._"
    ),
    STEP_CONFIRM: "",  # Built dynamically in ui.py
    STEP_DONE:    "",  # Built dynamically in ui.py
}

# Runtime token store — written by inject_token API, read by langflow_client
_api_key_store: dict = {}
_store_lock = threading.Lock()

def set_api_key(jwt_token: str) -> str:
    """
    Called by @gradio/client from your Node.js backend after JWT mint.
    
    Google Gemini API key is never shored to Gradio. Instead, we store the raw JWT token and only extract the API key at call time in NodeJS API, with exp>

    Do not store the JWT token anywhere in Gradio. If user refreshes the page, they will need to mint a new token and call this API again, which is good f>
    
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