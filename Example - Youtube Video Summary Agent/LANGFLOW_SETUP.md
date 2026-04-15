# Langflow Flow Setup Guide

This document explains how to create and connect the AI agent flow required by the
**YouTube Video Summarizer Agent** inside Langflow.
 
---

## A. How to Create the YouTube Summarizer Flow in Langflow

1. Open Langflow at your registered Codespace URL.
2. Click **New Flow → Blank Flow**.
3. Name it `Youtube Summarizer Agent` and save.
4. Copy the auto-generated **Flow ID** (visible in the URL or flow settings).
   Update `LANGFLOW_FLOW_ID` in `config.py` if it differs.
5. Find the **Google Generative AI component ID** and set
   `TWEAKS_API_GOOGLE_COMPONENT_ID` in `config.py`.
   (See [Section E](#e-finding-the-google-generative-ai-component-id) for instructions.)

### Flow Architecture

```
┌──────────────────────┐
│   Prompt Template    │  Contains the system prompt (see Section B)
└──────────────────────┘
           │  Prompt
           ▼
┌──────────────────────┐        ┌────────────────┐
│  Google Generative   │◄───────│  Chat Input    │  Receives [VIDEO TRANSCRIPT] + user message
│        AI            │        └────────────────┘
│  gemini-2.5-flash-   │
│  lite · 2000 tokens  │
│  temp 0.10           │
└──────────────────────┘
           │  Model Response
           ▼
┌──────────────────────┐
│     Chat Output      │  Returns the AI response to the Python app
└──────────────────────┘
```

The Prompt Template feeds the system instructions to the model.
The Python app injects the full video transcript into the Chat Input message
on the first call for any new video, then uses Langflow's session memory for
all follow-up questions.

---

## B. Required Components

| Component | Role |
|-----------|------|
| **Prompt Template** | Holds the system prompt that defines the agent's summariser behaviour |
| **Chat Input** | Receives the user message (with or without the video transcript prepended) |
| **Google Generative AI** | Language model that generates all AI responses |
| **Chat Output** | Returns the model response to the Python app via the REST API |

### Prompt Template Text

Paste the following into the **Template** field of the Prompt Template component:

```
You are a YouTube Video Summarizer assistant. Your job is to help users understand videos quickly.

When the user sends a message that begins with [VIDEO TRANSCRIPT], read that transcript carefully, then answer their question by:

1. Providing a **step-by-step breakdown** of what happens in the video (numbered, ≤ 2 sentences per step).
2. Adding a short **"📋 Prerequisites"** section listing tools/knowledge the viewer needs before following the video.
3. Adding a **"❓ You might want to ask next:"** section with 2-3 specific follow-up questions the user can paste back.

For follow-up messages (no transcript header), answer the specific question concisely and practically.

Rules:
- Be concise. Users want to skip watching the video.
- Use Markdown headers and bullet points.
- Never reproduce the raw transcript.
```

### Recommended Model Settings

| Setting | Value |
|---------|-------|
| **Model** | `gemini-2.5-flash-lite` |
| **Max Output Tokens** | `2000` |
| **Temperature** | `0.10` (Precise) |

> **Why `gemini-2.5-flash-lite`?** Summarisation is a structured extraction task with a
> predictable output length. The Lite model is faster and cheaper while producing
> output quality that is indistinguishable from the full Flash model for this use case.

---

## C. How the App Uses the Single Flow

The flow is called **twice** for each new video, then once per follow-up question:

```
[User pastes YouTube URL + question]
         │
         │  Python fetches transcript via MySphere proxy
         ▼
[VIDEO TRANSCRIPT]
<full transcript text>

[USER MESSAGE]
<user's question>
         │
         │  Call 1 — transcript + question → summary + prerequisites + follow-up suggestions
         ▼
   Langflow Flow ──► step-by-step summary

[User asks a follow-up question]
         │
         │  Call 2+ — question only (Langflow session memory retains context)
         ▼
   Langflow Flow ──► concise follow-up answer
```

---

## D. How to Connect the Flow via API

### Environment Variables

Set in your shell or a `.env` file before running `app.py`:

```bash
LANGFLOW_BASE_URL="https://api.mysphere.net"         # Do not change this URL
LANGFLOW_API_KEY="your-langflow-api-token"           # From Langflow → Settings → API Keys
LANGFLOW_FLOW_ID="your-flow-id"
TWEAKS_API_GOOGLE_COMPONENT_ID="component-xxxxxx"    # See Section E
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
  "input_value": "<[VIDEO TRANSCRIPT]\n...\n\n[USER MESSAGE]\n...>",
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

*No AI logic is hard-coded in the Python application. All LLM calls go through
Langflow. To change the summarisation style or output format, update the
Prompt Template in Langflow — no Python changes required.*

**Did You Notice?**
In the previous example of Exam Stratergy Agent we passed the System Instruction to the AI from Python code itself. In this example we have introduced another component in Langflow called as Prompt Template. This prompt template is used to give System Instructions to the AI directly in Langflow.