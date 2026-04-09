"""
app.py — Gradio UI for the YouTube Video Summarizer Agent.

Run this file to start the app:
    python app.py

The app opens at http://localhost:7861 in your browser.

─────────────────────────────────────────────────────────────────────────────
HOW TO USE THE STRETCH FEATURE
─────────────────────────────────────────────────────────────────────────────
There is one stretch feature in this file: the Prerequisites Prompt Panel.
It is fully written and working — it just needs to be switched on.

To activate it:
  Step 1 — In this file, find the block labelled "STRETCH: Prerequisites
            Prompt Panel" and uncomment it (select all lines, press Ctrl+/).
  Step 2 — Update your Langflow Prompt Template node with the extra
            instruction described inside that block.

That's it. No other changes are needed.
─────────────────────────────────────────────────────────────────────────────
"""

import uuid
import gradio as gr

from chat_handler import respond, clear_chat, send_to_agent
from config import set_api_key


# ── UI text constants ──────────────────────────────────────────────────────
HEADER = """# 🎬 YouTube Video Summarizer Agent

Paste a YouTube link anywhere in your message and ask a question.
The AI reads the **full transcript** and gives you a step-by-step summary — no watching required.

> **Example:** *"Here is the video https://youtu.be/Qbxm9mD-G18 — can you summarise it step by step?"*
"""

EXAMPLE_PROMPTS = [
    "Here is a YouTube video https://youtu.be/Qbxm9mD-G18?si=X2AwwU1RLcM-knjh — can you give me a short step-by-step explanation of what's happening?",
    "Can you explain step 2 in more detail?",
    "What are the key takeaways from this video?",
]


# ════════════════════════════════════════════════════════════════════════════
# Gradio UI
# ════════════════════════════════════════════════════════════════════════════
with gr.Blocks(title="YouTube Video Summarizer", theme=gr.themes.Soft(primary_hue="blue")) as demo:

    # ── Invisible state stored in the browser tab ─────────────────────────
    # These hold the current video transcript and conversation session ID.
    # They are NOT visible in the UI but are passed to every handler function.
    transcript_state = gr.State("")
    session_id       = gr.State(str(uuid.uuid4()))

    gr.Markdown(HEADER)

    with gr.Row():

        # ════════════════════════════════════════════════════════════════════
        # LEFT COLUMN — Chat panel
        # ════════════════════════════════════════════════════════════════════
        with gr.Column(scale=3):

            # ── Shared display components ─────────────────────────────────
            # These two components receive output from EVERY feature below.
            # Do NOT remove them — all buttons write their results here.
            chatbot    = gr.Chatbot(label="Conversation", height=520,
                                    placeholder="Your conversation will appear here…")
            status_box = gr.Textbox(value="Ready", label="Status", interactive=False)
            # ─────────────────────────────────────────────────────────────

            # ════════════════════════════════════════════════════════════════
            # FEATURE: Message input and Send button
            # ─────────────────────────────────────────────────────────────
            # To remove this feature: delete from here to END FEATURE below.
            # ════════════════════════════════════════════════════════════════
            with gr.Row():
                msg_box = gr.Textbox(
                    placeholder=(
                        "Paste a YouTube link with your question…\n"
                        "E.g. Here is https://youtu.be/xyz — what happens step by step?"
                    ),
                    label="Your message",
                    lines=3, scale=5, container=False,
                )
                send_btn = gr.Button("Send ➤", variant="primary", scale=1, min_width=90)

            _outputs = [chatbot, transcript_state, session_id, status_box]

            send_btn.click(
                fn=respond,
                inputs=[msg_box, chatbot, transcript_state, session_id],
                outputs=_outputs,
            ).then(lambda: "", outputs=msg_box)

            msg_box.submit(
                fn=respond,
                inputs=[msg_box, chatbot, transcript_state, session_id],
                outputs=_outputs,
            ).then(lambda: "", outputs=msg_box)
            # ═══════════════════════════ END FEATURE ═════════════════════

            # ════════════════════════════════════════════════════════════════
            # FEATURE: Clear chat button
            # ─────────────────────────────────────────────────────────────
            # To remove this feature: delete from here to END FEATURE below.
            # ════════════════════════════════════════════════════════════════
            clear_btn = gr.Button("🗑  Clear chat", variant="secondary")

            clear_btn.click(
                fn=clear_chat,
                inputs=[transcript_state, session_id],
                outputs=[chatbot, transcript_state, session_id, status_box],
            )

            # ════════════════════════════════════════════════════════════════
            # FEATURE: Hidden token injection endpoint for Google Gemini API key
            # ─────────────────────────────────────────────────────────────
            # To remove this feature: delete from here to END FEATURE below.
            # ════════════════════════════════════════════════════════════════ 
            # Hidden token injection endpoint — no UI component
            gr.api(set_api_key, api_name="inject_token")
            # ═══════════════════════════ END FEATURE ═════════════════════   

            # ════════════════════════════════════════════════════════════════
            # STRETCH: Prerequisites Prompt Panel
            # ─────────────────────────────────────────────────────────────
            # HOW TO ACTIVATE — 2 steps:
            #
            # STEP 1 — Uncomment this block.
            #           Select all lines from "with gr.Accordion" down to
            #           "prereq_btn.click(...)" and press Ctrl+/ to uncomment.
            #
            # STEP 2 — Open your Langflow flow, click the Prompt Template node,
            #           and add the following text to the system prompt field:
            #
            #   "When the user asks for prerequisites, list every tool, software,
            #    or concept a complete beginner must have before starting the steps
            #    in the video. For each item, include a short explanation of why
            #    it is needed and how to get or install it. Format as a numbered
            #    list. If the user then asks a follow-up question about any
            #    specific prerequisite (for example: how to install Node.js, or
            #    what is npm), answer that question fully even if it goes beyond
            #    the video content. Do not redirect the user back to the video
            #    summary when answering prerequisite questions."
            #
            # After both steps, a collapsible panel appears below the Send button.
            # The user can edit the question before sending it to the agent.
            # ════════════════════════════════════════════════════════════════

            # with gr.Accordion("🔧 Ask About Prerequisites", open=False):
            #     gr.Markdown(
            #         "The agent will list everything a beginner needs before "
            #         "starting the steps shown in the video. "
            #         "Edit the question below if you want to ask something more specific."
            #     )
            #     prereq_prompt_box = gr.Textbox(
            #         value=(
            #             "Based on the video, what are all the prerequisites "
            #             "a complete beginner needs before following these steps? "
            #             "For each one, explain why it is needed and how to get it."
            #         ),
            #         label="Prerequisites question (you can edit this)",
            #         lines=4,
            #     )
            #     prereq_btn = gr.Button("Ask Agent", variant="primary")
            #
            #     prereq_btn.click(
            #         fn=send_to_agent,
            #         inputs=[prereq_prompt_box, chatbot, transcript_state, session_id],
            #         outputs=[chatbot, transcript_state, session_id, status_box],
            #     )
            # ═══════════════════════ END STRETCH ═════════════════════════

        # ════════════════════════════════════════════════════════════════════
        # RIGHT COLUMN — Info and example prompts panel
        # ════════════════════════════════════════════════════════════════════
        with gr.Column(scale=1):

            # ════════════════════════════════════════════════════════════════
            # FEATURE: Example prompt buttons
            # ─────────────────────────────────────────────────────────────
            # To remove this feature: delete from here to END FEATURE below.
            # ════════════════════════════════════════════════════════════════
            # gr.Markdown("### 💡 Example prompts")
            # for prompt in EXAMPLE_PROMPTS:
            #     label = prompt[:65] + ("…" if len(prompt) > 65 else "")
            #     gr.Button(label, size="sm").click(fn=lambda p=prompt: p, outputs=msg_box)
            # ═══════════════════════════ END FEATURE ═════════════════════

            gr.Markdown(
                "---\n"
                "### ℹ️ How it works\n"
                "1. **Paste** a YouTube link in your message\n"
                "2. **Ask** any question about the video\n"
                "3. AI reads the transcript and summarises\n"
                "4. **Follow up** — ask for more detail, steps, etc.\n\n"
                "---\n"
                "### ⚙️ Powered by\n"
                "- [Supadata.ai](https://supadata.ai) — transcripts\n"
                "- [Langflow](https://langflow.org) — LLM flow\n"
            )

    # gr.Examples(
    #     examples=[[p] for p in EXAMPLE_PROMPTS],
    #     inputs=msg_box,
    #     label="Quick-start examples",
    # )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7861, 
        share=True
    )