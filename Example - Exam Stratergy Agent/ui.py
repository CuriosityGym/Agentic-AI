"""
ui.py
─────
Gradio UI — layout, components, and event wiring.

Each UI section has its own builder function so you can:
  • Remove a section: comment out its call in build_app()
  • Modify a section: edit only its builder, nothing else changes
  • Add a section: write a new builder and call it in build_app()

Section builders
────────────────
  build_header()          title and how-to-use instructions
  build_chatbot()         the main chat window
  build_input_box()       text + PDF file input
  build_action_buttons()  Clear Chat button (add more buttons here)
  build_quick_examples()  clickable example prompts panel
  build_status_bar()      status text line at the bottom
"""

import gradio as gr
from router import chat, STAGE_STATUS_LABELS
from config import set_api_key


# ─── Section builders ──────────────────────────────────────────────────────────

def build_header():
    """Title and how-to-use instructions shown above the chatbot."""
    gr.Markdown("""
## 📚 Exam Preparation Coach
**How to use:**
1. 📎 Attach your exam PDF + type a message → hit **Send**
2. Review the exam summary, then type **`start`** to begin the test
3. Answer each question one by one with **A**, **B**, **C**, or **D**
4. After all questions, get your score, wrong-answer explanations, strategy & weak topics!
""")


def build_chatbot() -> gr.Chatbot:
    """
    The main chat display window.
    latex_delimiters enables LaTeX math rendering inside assistant messages.
    """
    return gr.Chatbot(
        label="Exam Coach",
        height=715,
        render_markdown=True,
        autoscroll=True,
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},
            {"left": "$",  "right": "$",  "display": False},
        ],
        avatar_images=(
            None,
            "https://api.dicebear.com/7.x/bottts/svg?seed=coach",
        ),
    )


def build_input_box() -> gr.MultimodalTextbox:
    """
    The message input area. Accepts text and a single PDF file.
    Change file_types here if you want to support other formats later.
    """
    return gr.MultimodalTextbox(
        placeholder="Type your message or answer here... attach PDF with 📎",
        file_types=[".pdf"],
        file_count="single",
        show_label=False,
        scale=10,
        submit_btn=True,
    )


def build_action_buttons() -> gr.Button:
    """
    Action buttons row.
    To add a new button: create it here, return it, and wire it in build_app().
    """
    with gr.Row():
        clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary", scale=1)
    return clear_btn


def build_quick_examples(textbox: gr.MultimodalTextbox):
    """
    Clickable example prompts shown below the chat window.
    To add an example: append {"text": "your prompt"} to the list.
    To remove the entire panel: comment out this call in build_app().
    """
    gr.Examples(
        examples=[
            {"text": "start"},
            {"text": "A"},
            {"text": "B"},
            {"text": "Explain the concept behind question 5"},
            {"text": "What is the best strategy to attempt a JEE paper?"},
            # STRETCH 2.A: uncomment the line below once activated
            # {"text": "Explain why option A is correct for Question 3"},
            # STRETCH 2.B: uncomment the line below once activated
            # {"text": "Generate 3 more questions on Thermodynamics"},
        ],
        inputs=textbox,
        label="Quick inputs (click to use):",
    )


def build_status_bar() -> gr.Markdown:
    """
    Single-line status text updated after every message.
    The text values come from STAGE_STATUS_LABELS in router.py.
    """
    return gr.Markdown(
        "_Status: ⏳ Waiting for PDF upload..._",
        elem_id="status",
    )


# ─── Event handlers ───────────────────────────────────────────────────────────

def respond(message, history, state):
    """
    Called by Gradio on every submitted message.
    Builds the user-visible chat turn, calls the router, updates the status bar.
    """
    user_text = message.get("text", "") or ""
    if message.get("files"):
        user_text = (user_text + " 📎 [PDF attached]").strip()

    history = list(history) + [{"role": "user", "content": user_text}]
    reply, updated_state = chat(message, history, state)
    history = history + [{"role": "assistant", "content": reply}]

    stage = updated_state.get("stage", "awaiting_pdf")
    label = STAGE_STATUS_LABELS.get(stage, "")

    # For the in_test stage, append the live question progress count
    if stage == "in_test":
        answered = updated_state.get("current_q_index", 0)
        total    = len(updated_state.get("questions_order", []))
        label    = f"🎯 In test — Question {answered} of {total} answered"

    status_text = f"_Status: {label}_"
    return history, updated_state, gr.MultimodalTextbox(value=None), status_text


def clear_all():
    """Reset chat and state back to the initial empty session."""
    return [], {}, gr.MultimodalTextbox(value=None), "_Status: ⏳ Waiting for PDF upload..._"


# ─── App builder ──────────────────────────────────────────────────────────────
# SCROLL_JS = """
# () => {
#     function attachScrollObserver() {
#         const containers = document.querySelectorAll('.chatbot .overflow-y-auto');
#         if (!containers.length) { setTimeout(attachScrollObserver, 500); return; }
#         containers.forEach(container => {
#             new MutationObserver(() => {
#                 container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
#             }).observe(container, { childList: true, subtree: true });
#         });
#     }
#     attachScrollObserver();
# }
# """
def build_app() -> gr.Blocks:
    css = """
    /* Make the chatbot scrollbar always visible */
    .chatbot .overflow-y-auto::-webkit-scrollbar { width: 6px; }
    .chatbot .overflow-y-auto::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
    """
    # css = """
    #     /* Fix gr.Examples escaping column layout on first load */
    #     .examples-holder, .examples { width: 100% !important; overflow-x: hidden; }

    #     /* Chatbot scrollbar — Gradio 6.x compatible selectors */
    #     .chatbot > div { scroll-behavior: smooth; }
    #     .chatbot > div::-webkit-scrollbar { width: 6px; }
    #     .chatbot > div::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
    # """

    with gr.Blocks(title="Exam Strategy Coach", css=css) as demo:

        state = gr.State({})

        with gr.Row(equal_height=False):

            # ── Left column: header / instructions ───────────────────────────
            with gr.Column(scale=1, min_width=220):
                build_header()

            # ── Middle column: chat + input + controls ────────────────────────
            with gr.Column(scale=2, min_width=400):
                chatbot   = build_chatbot()
                textbox   = build_input_box()
                clear_btn = build_action_buttons()
                status_bar = build_status_bar()

            # ── Right column: quick examples ──────────────────────────────────
            with gr.Column(scale=1, min_width=220):
                build_quick_examples(textbox)

        # ── Wire events ───────────────────────────────────────────────────────
        textbox.submit(
            fn=respond,
            inputs=[textbox, chatbot, state],
            outputs=[chatbot, state, textbox, status_bar],
        )

        clear_btn.click(
            fn=clear_all,
            outputs=[chatbot, state, textbox, status_bar],
        )

        # Hidden token injection endpoint — no UI component
        gr.api(set_api_key, api_name="inject_token")

    return demo