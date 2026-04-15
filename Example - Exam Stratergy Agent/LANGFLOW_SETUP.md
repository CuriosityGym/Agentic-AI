# Langflow Flow Setup Guide

This document explains how to create and connect the AI agent flow required by the
**Exam Strategy Agent** inside Langflow.

---

## A. How to Create the Exam Strategy Agent Flow in Langflow

1. Open Langflow at your registered Github Codespace URL.
2. Click **New Flow → Blank Flow**.
3. Name it `Exam Strategy Agent` and save.
4. Copy the auto-generated **Flow ID** (visible in the URL or flow settings).
   Update `FLOW_ID` in `config.py` if it differs.
5. Find the **Google Generative AI component ID** and set
   `TWEAKS_API_GOOGLE_COMPONENT_ID` in `config.py`.
   (See [Section D](#d-finding-the-google-generative-ai-component-id) for instructions.)

### Flow Architecture

```
[User Message / PDF Context]
         │
         ▼
┌────────────────┐
│  Chat Input    │  Receives the full prompt from the Python app
└────────────────┘
         │
         ▼
┌────────────────────────┐
│  Google Generative AI  │  gemini-2.5-flash  ·  50 000 tokens  ·  temp 0.10
└────────────────────────┘
         │
         ▼
┌────────────────┐
│  Chat Output   │  Returns the AI response to the Python app
└────────────────┘
```

The Python app manages all session logic (stages, state, scoring).
The Langflow flow is intentionally kept simple — one AI call pipeline —
so that all behaviour is controlled from Python, not from Langflow.

---

## B. Required Components

| Component | Role |
|-----------|------|
| **Chat Input** | Receives the full prompt (including PDF text and instructions) from the Python app |
| **Google Generative AI** | Language model that generates all AI responses |
| **Chat Output** | Returns the model response to the Python app via the REST API |


### Recommended Model Settings

| Setting | Value |
|---------|-------|
| **Model** | `gemini-2.5-flash` |
| **Max Output Tokens** | `50000` |
| **Temperature** | `0.10` (Precise) |

> **Why low temperature?** The flow handles structured tasks — answer key extraction,
> JSON question banks, and score analysis — that require deterministic, well-formatted
> output. A low temperature reduces hallucination and format errors.

---

## C. How the App Uses the Single Flow

The same flow is called **up to four times** per student session, each time with
a different purpose-built prompt as `input_value`:

```
[Student uploads PDF]
         │
         │  Prompt 1 — extract answer key, topic list, summary
         ▼
   Langflow Flow ──► TOTAL_QUESTIONS / ANSWER_KEY / TOPICS / SUMMARY
         │
         │  Prompt 2 — extract full question bank
         ▼
   Langflow Flow ──► JSON array of all questions (number, text, options, answer)
         │
         │  (Test runs locally — no LLM call needed per question)
         │
         │  Prompt 3 — score analysis after test completion
         ▼
   Langflow Flow ──► Score summary · wrong-answer explanations · weak topics · strategy
         │
         │  Prompt 4+ — free-form Q&A using PDF as context
         ▼
   Langflow Flow ──► conversational answer
```

---

## D. How to Connect the Flow via API

### Environment Variables

Set in your shell or a `.env` file before running `app_chat.py`:

```bash
export LANGFLOW_BASE_URL="https://api.mysphere.net"          # Do not change this URL
export LANGFLOW_API_KEY="your-langflow-api-token"            # From Langflow → Settings → API Keys
export LANGFLOW_FLOW_ID="your-flow-id"
export TWEAKS_API_GOOGLE_COMPONENT_ID="component-xxxxxx"     # See Section E
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
  "input_value": "<full prompt string>",
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

Each Langflow flow that uses a **Google Generative AI** component requires you to supply
its component ID so the app can send the correct `tweaks` payload.

1. Open the flow in Langflow.
2. Click on the **Google Generative AI** component to select it.
3. A small information box appears — hover over the ID field until it reads **"Click to Copy Full ID"**.
4. Click to copy. The ID looks like `component-123abc`.
5. Paste this value into `config.py` (or the corresponding env var):
   - `TWEAKS_API_GOOGLE_COMPONENT_ID`

---

*No AI logic is hard-coded in the Python application. All LLM calls go through
Langflow. To swap the model or adjust behaviour, update the flow in Langflow —
no Python changes required.*