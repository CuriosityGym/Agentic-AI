import logging

import gradio as gr

from config import (
    STEP_NAME_SCHOOL_GRADE, STEP_INTRODUCTION, STEP_LINKS, STEP_HOBBIES,
    STEP_INTERESTS, STEP_SKILLS, STEP_COURSES, STEP_PROJECTS, STEP_THEME,
    STEP_CONFIRM, STEP_DONE, STEP_PROMPTS,
)
from schema import new_student_data, validate_student_data
from parser import parse_links, parse_list, parse_name_school_grade
from file_writer import write_portfolio_files
from coder import run_portfolio_generation
from config import set_api_key

logger = logging.getLogger(__name__)


def _is_skip(text: str) -> bool:
    return text.strip().lower() in {"skip", "s", "no", "none", "n/a", "-"}


def _format_summary(data: dict) -> str:
    lines = [
        "## 📋 Your Portfolio Summary\n",
        f"**Name:** {data['name']}",
        f"**School:** {data['school']}",
        f"**Grade:** {data['grade']}",
        f"**Introduction:** {data['introduction']}",
    ]

    if data["links"]:
        links_str = ", ".join(f"{l['name'].title()}: {l['url']}" for l in data["links"])
        lines.append(f"**Links:** {links_str}")
    if data["hobbies"]:
        lines.append(f"**Hobbies:** {', '.join(data['hobbies'])}")
    if data["interests"]:
        lines.append(f"**Interests:** {', '.join(data['interests'])}")
    if data["skills"]:
        lines.append(f"**Skills:** {', '.join(data['skills'])}")
    if data["courses"]:
        lines.append(f"**Courses:** {', '.join(data['courses'])}")

    if data["projects"]:
        lines.append("\n**Projects:**")
        for p in data["projects"]:
            proj_line = f"  - **{p['name']}**: {p['description']}"
            if p.get("file_path"):
                proj_line += " _(file attached)_"
            lines.append(proj_line)

    if data["theme_preference"]:
        lines.append(f"\n**Theme:** {data['theme_preference']}")

    return "\n".join(lines)


def chat_handler(
    user_message: str,
    uploaded_file,
    history: list,
    student_data: dict,
    current_step: int,
) -> tuple[list, dict, int, gr.update, str | None]:
    history      = history or []
    student_data = student_data or new_student_data()
    zip_path     = None
    show_upload  = False

    history.append({"role": "user", "content": user_message})

    if current_step == STEP_NAME_SCHOOL_GRADE:
        name, school, grade = parse_name_school_grade(user_message)
        student_data["name"]   = name or user_message.strip()
        student_data["school"] = school
        student_data["grade"]  = grade
        next_step = STEP_INTRODUCTION
        bot_reply = STEP_PROMPTS[STEP_INTRODUCTION]

    elif current_step == STEP_INTRODUCTION:
        student_data["introduction"] = user_message.strip()
        next_step = STEP_LINKS
        bot_reply = STEP_PROMPTS[STEP_LINKS]

    elif current_step == STEP_LINKS:
        if not _is_skip(user_message):
            student_data["links"] = parse_links(user_message)
        next_step = STEP_HOBBIES
        bot_reply = STEP_PROMPTS[STEP_HOBBIES]

    elif current_step == STEP_HOBBIES:
        if not _is_skip(user_message):
            student_data["hobbies"] = parse_list(user_message)
        next_step = STEP_INTERESTS
        bot_reply = STEP_PROMPTS[STEP_INTERESTS]

    elif current_step == STEP_INTERESTS:
        if not _is_skip(user_message):
            student_data["interests"] = parse_list(user_message)
        next_step = STEP_SKILLS
        bot_reply = STEP_PROMPTS[STEP_SKILLS]

    elif current_step == STEP_SKILLS:
        if not _is_skip(user_message):
            student_data["skills"] = parse_list(user_message)
        next_step = STEP_COURSES
        bot_reply = STEP_PROMPTS[STEP_COURSES]

    elif current_step == STEP_COURSES:
        if not _is_skip(user_message):
            student_data["courses"] = parse_list(user_message)
        next_step   = STEP_PROJECTS
        show_upload = True
        bot_reply   = STEP_PROMPTS[STEP_PROJECTS]

    elif current_step == STEP_PROJECTS:
        if not _is_skip(user_message):
            projects = []
            for line in user_message.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                if "|" in line:
                    parts     = line.split("|", 1)
                    proj_name = parts[0].strip()
                    proj_desc = parts[1].strip()
                else:
                    proj_name = line
                    proj_desc = ""

                file_path = ""
                if uploaded_file is not None:
                    file_path = getattr(uploaded_file, "name", str(uploaded_file))

                projects.append({
                    "name":        proj_name,
                    "description": proj_desc,
                    "file_path":   file_path,
                })
            student_data["projects"] = projects

        next_step   = STEP_THEME
        show_upload = False
        bot_reply   = STEP_PROMPTS[STEP_THEME]

    elif current_step == STEP_THEME:
        valid_themes = {"dark", "light", "colorful", "minimal"}
        theme_input  = user_message.strip().lower()
        if theme_input in valid_themes:
            student_data["theme_preference"] = theme_input

        summary   = _format_summary(student_data)
        next_step = STEP_CONFIRM
        bot_reply = (
            f"{summary}\n\n"
            "---\n"
            "Do you want to generate your portfolio website?\n\n"
            "Type **yes** to proceed or **no** to restart."
        )

    elif current_step == STEP_CONFIRM:
        if user_message.strip().lower() in {"yes", "y", "sure", "ok", "okay", "generate"}:
            bot_reply = "⏳ Generating your portfolio… please wait."
            history.append({"role": "assistant", "content": bot_reply})

            is_valid, missing = validate_student_data(student_data)
            if not is_valid:
                error_msg = (
                    f"⚠️ Some required fields are missing: **{', '.join(missing)}**. "
                    "Please restart and fill them in."
                )
                history.append({"role": "assistant", "content": error_msg})
                return history, student_data, STEP_DONE, gr.update(visible=False), None

            try:
                files     = run_portfolio_generation(student_data)
                zip_path  = str(write_portfolio_files(files))
                next_step = STEP_DONE
                bot_reply = (
                    "✅ Your portfolio has been generated successfully!\n\n"
                    "Click the **Download Portfolio ZIP** button below to get your files.\n\n"
                    "Unzip and open `index.html` in any browser to preview your site."
                )
            except RuntimeError as exc:
                logger.error("Portfolio generation failed: %s", exc)
                next_step = STEP_CONFIRM
                bot_reply = f"❌ Something went wrong. Please try again.\n\n_{exc}_"
        else:
            next_step    = STEP_NAME_SCHOOL_GRADE
            student_data = new_student_data()
            bot_reply    = "No problem! Let's start over.\n\n" + STEP_PROMPTS[STEP_NAME_SCHOOL_GRADE]

    else:
        # STEP_DONE or unknown – restart
        next_step    = STEP_NAME_SCHOOL_GRADE
        student_data = new_student_data()
        bot_reply    = "Starting a new portfolio. " + STEP_PROMPTS[STEP_NAME_SCHOOL_GRADE]

    history.append({"role": "assistant", "content": bot_reply})
    return history, student_data, next_step, gr.update(visible=show_upload), zip_path


def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Personal Portfolio Website Builder",
        theme=gr.themes.Soft(),
        css="""
        #chat-col { max-width: 860px; margin: 0 auto; }
        #title    { text-align: center; margin-bottom: 4px; }
        #subtitle { text-align: center; color: #666; margin-bottom: 20px; }
        """,
    ) as demo:

        # ── Header ──────────────────────────────────────────────────────────────
        gr.Markdown("# 🌐 Personal Portfolio Website Builder", elem_id="title")
        gr.Markdown(
            "Answer the questions below to build your personalised portfolio website.",
            elem_id="subtitle",
        )

        # ── Shared State ─────────────────────────────────────────────────────────
        # These hold data between chat turns. Do not remove them.
        student_data_state = gr.State(new_student_data())
        step_state         = gr.State(STEP_NAME_SCHOOL_GRADE)

        with gr.Column(elem_id="chat-col"):

            # ── Chatbot ──────────────────────────────────────────────────────────
            chatbot = gr.Chatbot(
                label="Portfolio Builder Chat",
                value=[{"role": "assistant", "content": STEP_PROMPTS[STEP_NAME_SCHOOL_GRADE]}],
                height=520,
                buttons=["copy"],
            )

            # ── File Upload (shown only during the Projects step) ─────────────────
            # To remove file upload: comment out this block and remove `file_upload`
            # from the inputs/outputs lists below.
            file_upload = gr.File(
                label="📎 Upload a project file (optional)",
                visible=False,
                file_types=[".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".txt", ".md"],
            )

            # ── Message input + Send button ───────────────────────────────────────
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Type your answer here…",
                    label="",
                    lines=2,
                    scale=8,
                    show_label=False,
                )
                submit_btn = gr.Button("Send ➤", variant="primary", scale=1)

            # ── Download button (hidden until portfolio is generated) ─────────────
            # To remove download: comment out this block and remove `download_file`
            # from the outputs lists below.
            download_file = gr.DownloadButton(
                label="📥 Download Portfolio ZIP",
                visible=False,
                variant="primary",
            )

            # ── Restart button ────────────────────────────────────────────────────
            # To remove restart: comment out this block entirely.
            restart_btn = gr.Button("🔄 Start Over", variant="secondary", size="sm")

        # ── Event: Send message ───────────────────────────────────────────────────
        def on_submit(user_msg, uploaded_file, history, student_data, current_step):
            if not user_msg.strip():
                return history, student_data, current_step, gr.update(), gr.update(visible=False), ""

            new_history, new_data, new_step, upload_vis, zip_path = chat_handler(
                user_msg, uploaded_file, history, student_data, current_step
            )
            download_update = (
                gr.update(value=zip_path, visible=True) if zip_path else gr.update(visible=False)
            )
            return new_history, new_data, new_step, upload_vis, download_update, ""

        submit_btn.click(
            fn=on_submit,
            inputs=[msg_input, file_upload, chatbot, student_data_state, step_state],
            outputs=[chatbot, student_data_state, step_state, file_upload, download_file, msg_input],
        )
        msg_input.submit(
            fn=on_submit,
            inputs=[msg_input, file_upload, chatbot, student_data_state, step_state],
            outputs=[chatbot, student_data_state, step_state, file_upload, download_file, msg_input],
        )

        # ── Event: Restart ────────────────────────────────────────────────────────
        def on_restart():
            return (
                [{"role": "assistant", "content": STEP_PROMPTS[STEP_NAME_SCHOOL_GRADE]}],
                new_student_data(),
                STEP_NAME_SCHOOL_GRADE,
                gr.update(visible=False),
                gr.update(visible=False),
                "",
            )

        restart_btn.click(
            fn=on_restart,
            inputs=[],
            outputs=[chatbot, student_data_state, step_state, file_upload, download_file, msg_input],
        )

        # Hidden token injection endpoint — no UI component
        gr.api(set_api_key, api_name="inject_token")

        # ── ADDON AREA ────────────────────────────────────────────────────────────
        # Add new UI sections here. Follow this pattern:
        #   1. Define your Gradio component(s)
        #   2. Define your event handler function directly below it
        #   3. Wire the event: component.event(fn=handler, inputs=[...], outputs=[...])
        # Each section should be self-contained so it can be commented out safely.
        # ─────────────────────────────────────────────────────────────────────────

    return demo