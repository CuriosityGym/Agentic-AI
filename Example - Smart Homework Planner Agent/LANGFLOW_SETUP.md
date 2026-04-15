# Langflow Flow Setup Guide

This document explains how to create and connect the AI agent flow required by the
**Smart Homework Planner** inside Langflow.

---

## A. How to Create the Homework Planner Flow in Langflow

1. Open Langflow at your registered Codespace URL.
2. Click **New Flow → Blank Flow**.
3. Name it `Homework Planner Agent` and save.
4. Copy the auto-generated **Flow ID** (visible in the URL or flow settings).
   Update `LANGFLOW_FLOW_ID` in `config.py` if it differs.
5. Find the **Google Generative AI component ID** and set
   `TWEAKS_API_GOOGLE_COMPONENT_ID` in `config.py`.
   (See [Section E](#e-finding-the-google-generative-ai-component-id) for instructions.)

### Flow Architecture

```
┌────────────────────────┐
│    Prompt Template     │  Contains the scheduling system prompt (see Section B)
└────────────────────────┘
            │  Prompt
            ▼
┌────────────────────────┐        ┌────────────────┐
│   Google Generative    │◄───────│  Chat Input    │  Receives JSON scheduling payload
│          AI            │        └────────────────┘
└────────────────────────┘
            │  Model Response
            ▼
┌────────────────────────┐
│      Chat Output       │  Returns JSON back to the Python app
└────────────────────────┘
```

The Python app serialises all calendar events, homework tasks, and constraints into
a single JSON object and sends it as `input_value`. The flow returns a JSON object
with `scheduled` and `unscheduled` arrays. If Langflow is unreachable, the app
automatically falls back to a local Python scheduler — no data is lost.

---

## B. Required Components

| Component | Role |
|-----------|------|
| **Prompt Template** | Holds the scheduling system prompt with the rules and output format |
| **Chat Input** | Receives the serialised JSON payload from the Python app |
| **Google Generative AI** | Language model that produces the scheduling JSON |
| **Chat Output** | Returns the model response to the Python app via the REST API |

### Prompt Template Text

Paste the following into the **Template** field of the Prompt Template component:

```
You are a homework scheduling assistant.
You will receive a JSON object with these fields:
  - events: list of calendar blocks with start/end ISO timestamps
  - tasks: list of homework tasks with name, duration_minutes, due_date
  - constraints: max_sessions_per_day, max_session_minutes, timezone
  - start_date / end_date: scheduling window (Mon–Fri only)

Rules:
1. Only schedule between 07:00–21:00 local time.
2. Skip any free gap shorter than 15 minutes.
3. Max {max_sessions_per_day} sessions per day.
4. Each session is at most {max_session_minutes} minutes.
5. Tasks may be split across multiple sessions.
6. Prioritise earliest due_date first (greedy fill).
7. Do NOT schedule on weekends.

Input JSON:
{input}

Return ONLY a valid JSON object — no markdown, no explanation:
{"scheduled": [...], "unscheduled": [...]}

Each scheduled item:
{"task": "<name>", "start": "<ISO>", "end": "<ISO>", "duration_minutes": <int>}
Each unscheduled item:
{"name": "<name>", "remaining_minutes": <int>}
```

### Recommended Model Settings

| Setting | Value |
|---------|-------|
| **Model** | `gemini-2.5-flash` |
| **Max Output Tokens** | `8192` |
| **Temperature** | `0.10` (Precise) |

> **Why low temperature?** The flow must return machine-readable JSON every time.
> A low temperature minimises the chance of the model adding prose, markdown fences,
> or malformed output that would break JSON parsing in the Python app.

---

## C. How the App Uses the Flow

```
[User uploads .ics calendar + homework CSV]
         │
         │  Python parses both files locally
         ▼
{
  "events":      [...],   ← existing calendar blocks
  "tasks":       [...],   ← homework tasks from CSV
  "constraints": {...},   ← max sessions/day, max duration, timezone
  "start_date":  "...",
  "end_date":    "..."
}
         │
         │  POST to Langflow as input_value (JSON string)
         ▼
   Langflow Flow ──► {"scheduled": [...], "unscheduled": [...]}
         │
         │  Python merges sessions with original events
         ▼
   ics_generator.py ──► smart_homework_schedule_<uuid>.ics
         │
         ▼
   User downloads .ics and imports into Thunderbird
```

**Fallback behaviour:** if `LANGFLOW_FLOW_ID` is not set or the Langflow server
is unreachable, the app runs the same scheduling logic locally via `scheduler.py`
and still produces a valid `.ics` file.

---

## D. How to Connect the Flow via API

### Environment Variables

Set in your shell or a `.env` file before running `app.py`:

```bash
export LANGFLOW_URL="https://api.mysphere.net"           # Do not change this URL
export LANGFLOW_API_KEY="your-langflow-api-token"        # From Langflow → Settings → API Keys
export LANGFLOW_FLOW_ID="your-flow-id"
export TWEAKS_API_GOOGLE_COMPONENT_ID="component-xxxxxx" # See Section E
```

### Obtaining a Langflow API Token

1. In Langflow, go to **Settings → API Keys**.
2. Create a new key and copy the token.
3. Set it as `LANGFLOW_API_KEY` (see above).

### API Call Structure

The Python client (`langflow_client.py`) POSTs to:

```
POST https://api.mysphere.net/api/v1/proxy/langflow/run/{flow_id}
Content-Type: application/json
x-api-key: <LANGFLOW_API_KEY>
gradio-token: <your-gradio-api-key>

{
  "input_value": "{\"events\":[...],\"tasks\":[...],\"constraints\":{...}}",
  "input_type":  "chat",
  "output_type": "chat",
  "session_id":  "<unique-session-id>",
  "tweaks": [
    {
      "component_id": "<TWEAKS_API_GOOGLE_COMPONENT_ID>",
      "parameters": {
        "type": "google_generative_ai"
      }
    }
  ]
}
```

---

## E. Finding the Google Generative AI Component ID

The app requires the **Google Generative AI** component's ID to target it correctly
in the `tweaks` payload.

1. Open the flow in Langflow.
2. Click on the **Google Generative AI** component to select it.
3. A small information box appears — hover over the ID field until it reads
   **"Click to Copy Full ID"**.
4. Click to copy. The ID looks like `component-123abc`.
5. Paste this value into `config.py` (or the corresponding env var):
   - `TWEAKS_API_GOOGLE_COMPONENT_ID`

---

## F. Using the Generated Schedule in Thunderbird

### Exporting Your Existing Calendar from Thunderbird

1. Open **Thunderbird** and switch to the **Calendar** view.
2. Right-click the calendar you want to export in the left-hand panel.
3. Select **Export…**
4. Save the file with a `.ics` extension (e.g. `my_calendar.ics`).
5. Upload this file as **Step 1** in the Smart Homework Planner app.

### Importing the Generated Schedule into Thunderbird

After the app generates `smart_homework_schedule_<uuid>.ics` and you download it:

1. In Thunderbird **Calendar** view, go to **Events and Tasks → Import…**
2. Browse to the downloaded `.ics` file and click **Open**.
3. Choose which calendar to add the events to and click **OK**.
4. Your study sessions (labelled **📚 Study: \<task name\>**) will now appear
   in your calendar alongside your existing events.

> **Tip:** Import into a dedicated **"Homework"** calendar in Thunderbird so you
> can show/hide study sessions independently from your other events.

---

*No scheduling logic is hard-coded in the Langflow flow. The Python app enforces
all constraints locally and also provides a full local fallback. Langflow is used
as the AI scheduling layer when available — to adjust scheduling rules, update the
Prompt Template in Langflow.*