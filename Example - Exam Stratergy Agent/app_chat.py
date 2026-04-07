"""
app_chat.py
───────────
Entry point. Run this file to start the Exam Preparation Coach:

    python app_chat.py

Configure the Langflow connection in config.py, or via environment variables:

    LANGFLOW_BASE_URL  (default: http://127.0.0.1:7860)
    LANGFLOW_API_KEY
    LANGFLOW_FLOW_ID

─── Read the files in this order to understand the codebase ───────────────────
  1. config.py           — all settings + session state schema (start here)
  2. langflow_client.py  — how the app sends prompts to the AI
  3. pdf_handler.py      — Feature: PDF upload and analysis
  4. test_engine.py      — Feature: scored test, one question at a time
  5. followup_handler.py — Feature: free Q&A + stretch goal scaffolding
  6. router.py           — which handler runs for each stage
  7. ui.py               — Gradio layout, components, and event wiring
  8. app_chat.py         — this file (launch settings only)
───────────────────────────────────────────────────────────────────────────────
"""

import gradio as gr
from ui import build_app

if __name__ == "__main__":
    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=True,
        show_error=True,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="indigo",
        ),
        css="""
        .gradio-container { max-width: 900px !important; margin: auto; }
        .message-row { font-size: 15px; }
        footer { display: none !important; }
        """,
    )