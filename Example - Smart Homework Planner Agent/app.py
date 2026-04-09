"""Smart Homework Planner – Gradio UI entry point."""
import os, traceback, uuid, tempfile
from datetime import date, timedelta
import gradio as gr

from config import APP_TITLE, LANGFLOW_FLOW_ID, set_api_key
from calendar_parser import parse_ics
from csv_parser import parse_homework_csv
from planner_agent import run_planner_agent
from calendar_agent import run_calendar_agent
from langflow_client import is_langflow_available, run_langflow_planner

# ── Welcome message shown in the chatbot on first load ────────────────────────
WELCOME_MESSAGE = (
    "👋 Welcome to **Smart Homework Planner**!\n\n"
    "**Step 1 →** Upload your `.ics` calendar file.\n\n"
    "**Step 2 →** Upload your homework tasks CSV.\n\n"
    "Adjust the constraints on the right, then click **▶ Generate Schedule**."
)

# ── Shared pipeline (called by the Generate handler) ─────────────────────────
def _run_pipeline(events, tasks, max_sessions, max_duration, timezone, session_id=None):
    constraints = {
        "max_sessions_per_day": max_sessions,
        "max_session_minutes": max_duration,
        "timezone": timezone,
    }
    start_date = min(e["start"].date() for e in events) if events else date.today()
    end_date   = max(e["end"].date()   for e in events) if events else start_date + timedelta(days=4)

    scheduled, unscheduled, used_langflow = [], [], False

    if LANGFLOW_FLOW_ID and is_langflow_available():
        try:
            payload = {
                "events":      [{"summary": e["summary"], "start": e["start"].isoformat(), "end": e["end"].isoformat()} for e in events],
                "tasks":       [{"name": t["name"], "duration_minutes": t["duration_minutes"], "due_date": t["due_date"].isoformat()} for t in tasks],
                "constraints": constraints,
                "start_date":  start_date.isoformat(),
                "end_date":    end_date.isoformat(),
            }
            result       = run_langflow_planner(payload, session_id=session_id)
            scheduled    = result.get("scheduled", [])
            unscheduled  = result.get("unscheduled", [])
            used_langflow = True
        except Exception:
            pass  # fall through to local agents

    if not used_langflow:
        result      = run_planner_agent(events, tasks, constraints, start_date, end_date)
        scheduled   = result["scheduled"]
        unscheduled = result["unscheduled"]

    ics_path = run_calendar_agent(events, scheduled, timezone)
    return scheduled, unscheduled, ics_path


# ── Build the Gradio UI ───────────────────────────────────────────────────────
with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft()) as demo:

    gr.Markdown(f"# 📚 {APP_TITLE}")

    # Shared state – persists across all handler calls
    app_state = gr.State({"stage": "init", "events": None, "session_id": str(uuid.uuid4())})

    with gr.Row():
        with gr.Column(scale=3):

            # ── CHATBOT ───────────────────────────────────────────────────────
            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": WELCOME_MESSAGE}],
                height=460,
                label="Planner Assistant",
            )

            with gr.Row():
                # ── ICS UPLOAD ────────────────────────────────────────────────
                # Handler: validates the .ics file and enables the CSV uploader
                def on_ics_upload(ics_file, history, state):
                    if ics_file is None:
                        return history, state, gr.update(interactive=False)
                    path = ics_file if isinstance(ics_file, str) else getattr(ics_file, "name", None)
                    try:
                        events = parse_ics(path)
                        state  = {**state, "events": events, "stage": "ics_uploaded"}
                        days   = sorted({e["start"].date() for e in events})
                        span   = f"{days[0]} → {days[-1]}" if len(days) > 1 else str(days[0]) if days else "unknown"
                        msg    = f"✅ Calendar loaded! Found **{len(events)} event(s)** spanning {span}.\n\nNow upload your **homework CSV**."
                        csv_state = gr.update(interactive=True)
                    except ValueError as exc:
                        state = {**state, "stage": "init"}
                        msg   = f"❌ Could not read file:\n\n`{exc}`"
                        csv_state = gr.update(interactive=False)
                    return history + [{"role": "assistant", "content": msg}], state, csv_state

                ics_upload = gr.File(label="Step 1 – Upload Calendar (.ics)", file_types=[".ics"])

                # ── CSV UPLOAD ────────────────────────────────────────────────
                # No handler here – CSV is read inside the Generate handler below
                csv_upload = gr.File(label="Step 2 – Upload Homework CSV", file_types=[".csv"], interactive=False)

            with gr.Row():
                # ── GENERATE BUTTON ───────────────────────────────────────────
                # Handler: parses CSV, runs pipeline, returns result + download
                def on_generate(csv_file, history, state, max_sessions, max_duration, timezone):
                    no_file = gr.update(visible=False, value=None)
                    if state.get("stage") != "ics_uploaded":
                        return history + [{"role": "assistant", "content": "⚠️ Upload your `.ics` file first."}], state, no_file
                    if csv_file is None:
                        return history + [{"role": "assistant", "content": "⚠️ Upload your homework CSV."}], state, no_file
                    path = csv_file if isinstance(csv_file, str) else getattr(csv_file, "name", None)
                    try:
                        tasks = parse_homework_csv(path)
                    except ValueError as exc:
                        return history + [{"role": "assistant", "content": f"❌ Invalid CSV:\n```\n{exc}\n```"}], state, no_file

                    history = history + [{"role": "assistant", "content": f"⏳ Scheduling **{len(tasks)} task(s)**… please wait."}]
                    attempt_id = str(uuid.uuid4())
                    state = {**state, "session_id": attempt_id}
                    try:
                        scheduled, unscheduled, ics_path = _run_pipeline(
                            events=state.get("events", []), tasks=tasks,
                            max_sessions=int(max_sessions), max_duration=int(max_duration),
                            timezone=timezone.strip() or "UTC", session_id=attempt_id,
                        )
                    except Exception:
                        err = traceback.format_exc()
                        return history + [{"role": "assistant", "content": f"❌ Error:\n```\n{err}\n```"}], state, no_file

                    lines = [f"✅ Done! **{len(scheduled)} session(s)** planned.\n"]
                    for s in scheduled:
                        lines.append(f"- `{s['task']}`: {s['start'][:16].replace('T',' ')} → {s['end'][:16].replace('T',' ')} ({s['duration_minutes']} min)")
                    if unscheduled:
                        lines.append(f"\n⚠️ **{len(unscheduled)} task(s)** could not be fully scheduled:")
                        for t in unscheduled:
                            lines.append(f"- `{t['name']}`: {t['remaining_minutes']} min remaining")
                    lines.append("\n📥 Download your calendar below.")

                    state = {**state, "stage": "done", "output_path": ics_path}
                    return history + [{"role": "assistant", "content": "\n".join(lines)}], state, gr.update(value=ics_path, visible=True)

                generate_btn = gr.Button("▶  Generate Schedule", variant="primary", scale=3)

                # ── RESET BUTTON ──────────────────────────────────────────────
                # Handler: wipes all state and resets UI to initial state
                def on_reset(state):
                    return (
                        [{"role": "assistant", "content": WELCOME_MESSAGE}],
                        {"stage": "init", "events": None},
                        gr.update(value=None, interactive=True),
                        gr.update(value=None, interactive=False),
                        gr.update(visible=False, value=None),
                    )

                reset_btn = gr.Button("🔄  Reset", variant="secondary", scale=1)

        with gr.Column(scale=1, min_width=240):
            # ── SETTINGS PANEL ────────────────────────────────────────────────
            gr.Markdown("### ⚙️ Scheduling Constraints")
            max_sessions_slider = gr.Slider(minimum=1, maximum=4, value=2, step=1,  label="Max Study Sessions per Day")
            max_duration_slider = gr.Slider(minimum=15, maximum=180, value=60, step=15, label="Max Session Duration (minutes)")
            timezone_input      = gr.Textbox(value="UTC", label="Timezone (IANA)", placeholder="e.g. America/New_York")

            gr.Markdown("---")

            # ── DOWNLOAD ──────────────────────────────────────────────────────
            gr.Markdown("### 📥 Download")
            output_file = gr.DownloadButton(label="⬇️ Download Scheduled Calendar (.ics)", visible=False)

    # ── CSV FORMAT REFERENCE ──────────────────────────────────────────────────
    with gr.Accordion("📋 CSV Format Reference", open=False):
        gr.Markdown(
            "| name | duration_minutes | due_date |\n"
            "|------|-----------------|----------|\n"
            "| Math Homework | 60 | 2026-03-25 |\n\n"
            "- `duration_minutes` – total minutes needed\n"
            "- `due_date` – deadline in `YYYY-MM-DD` format"
        )

    # Hidden token injection endpoint — no UI component
    gr.api(set_api_key, api_name="inject_token")    

    # ── EVENT WIRING ──────────────────────────────────────────────────────────
    # Connect each component to its handler (must come after all components are defined)
    ics_upload.change(fn=on_ics_upload,
        inputs=[ics_upload, chatbot, app_state],
        outputs=[chatbot, app_state, csv_upload])

    generate_btn.click(fn=on_generate,
        inputs=[csv_upload, chatbot, app_state, max_sessions_slider, max_duration_slider, timezone_input],
        outputs=[chatbot, app_state, output_file])

    reset_btn.click(fn=on_reset,
        inputs=[app_state],
        outputs=[chatbot, app_state, ics_upload, csv_upload, output_file])    

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(server_port=7861, share=True, allowed_paths=[tempfile.gettempdir()])