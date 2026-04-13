# Langflow Flow Setup Guide

This document explains how to create and connect the two AI agent flows
required by the **Personal Portfolio Website Builder** inside Langflow.

---

## A. How to Create the Designer Flow in Langflow

1. Open Langflow at your registered Codespace URL.
2. Click **New Flow → Blank Flow**.
3. Name it `designer_flow` and save.
4. Copy the auto-generated **Flow ID** (visible in the URL or flow settings).
   Update `DESIGNER_FLOW_ID` in `config.py` if it differs.
5. Find the **Google Generative AI component ID** and set `DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID` in `config.py`. (See [Section E](#e-finding-google-generative-ai-component-ids) for instructions.)

### Designer Flow Purpose
Receives the full `student_data` JSON and produces a design specification:
```json
{
  "theme": "dark",
  "layout": "modern",
  "sections": ["about", "projects", "skills", "contact"]
}
```

---

## B. How to Create the Coder Flow in Langflow

1. Open Langflow at your registered Codespace URL.
2. Click **New Flow → Blank Flow**.
3. Name it `coder_flow` and save.
4. Copy the auto-generated **Flow ID** and set `CODER_FLOW_ID` in `config.py` accordingly.
5. Find the **Google Generative AI component ID** and set `CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID` in `config.py`. (See [Section E](#e-finding-google-generative-ai-component-ids) for instructions.)

### Coder Flow Purpose
Receives `student_data` + `design` spec and returns three website files:
```json
{
  "index.html": "<html>...</html>",
  "style.css": "body { ... }",
  "main.js": "console.log(...)"
}
```

---

## C. Required Components in Each Flow

### Designer Flow Components

| Component | Role |
|-----------|------|
| **Chat Input** | Receives the stringified `student_data` JSON |
| **Prompt** | System prompt instructing the model to produce a design JSON |
| **Google Generative AI** | Language model that generates the design spec |
| **JSON Parser** _(optional)_ | Ensures output is valid JSON |
| **Chat Output** | Returns the design spec to the API caller |

**Prompt template example:**
```
You are a website designer. Given the following student data, produce a JSON
design specification with keys: theme, layout, sections.

Student data:
{input_value}

Respond ONLY with valid JSON. No markdown, no explanation.
```

---

### Coder Flow Components

| Component | Role |
|-----------|------|
| **Chat Input** | Receives stringified `{"student_data": {...}, "design": {...}}` |
| **Prompt** | System prompt instructing the model to write HTML/CSS/JS |
| **Google Generative AI** | Language model that generates the website code |
| **JSON Parser** _(optional)_ | Validates the output JSON structure |
| **Chat Output** | Returns `{"index.html": "...", "style.css": "...", "main.js": "..."}` |

**Prompt template example:**
```
You are an expert web developer. Using the student data and design specification
below, generate a complete personal portfolio website.

Return ONLY valid JSON with exactly these three keys:
  "index.html"  – full HTML document (no external CDN dependencies)
  "style.css"   – all CSS styles
  "main.js"     – all JavaScript

Input:
{input_value}

Respond ONLY with valid JSON. No markdown, no explanation.
```

---

## D. How to Connect the Flows via API

### Environment Variables

Set in your shell or a `.env` file before running `app.py`:

```bash
export LANGFLOW_BASE_URL="https://api.mysphere.net"                           # Do not change this URL
export LANGFLOW_TOKEN="your-langflow-api-token"                               # From Langflow → Settings → API Keys
export DESIGNER_FLOW_ID="your-designer-flow-id"
export DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID="component-xxxxxx"        # See Section E
export CODER_FLOW_ID="your-coder-flow-id"
export CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID="component-xxxxxx"           # See Section E
```

### Obtaining a Langflow API Token

1. In Langflow, go to **Settings → API Keys**.
2. Create a new key and copy the token.
3. Set it as `LANGFLOW_TOKEN` (see above).

### API Call Structure

The Python client (`langflow_client.py`) POSTs to:

```
POST https://api.mysphere.net/api/v1/proxy/langflow/run/{flow_id}
Content-Type: application/json
x-api-key: <LANGFLOW_TOKEN>
gradio-token: <your-gradio-api-key>

{
  "input_value": "<stringified JSON payload>",
  "tweaks": [
    {
      "component_id": "<DESIGNER_or_CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID>",
      "parameters": {
        "type": "google_generative_ai"
      }
    }
  ]
}
```

### Flow Execution Order (handled automatically by the app)

```
[Student Data Collected]
        │
        ▼
┌─────────────────────┐
│  Designer Agent      │  POST /api/v1/run/designer_flow
│  Input: student_data │──────────────────────────────► Langflow
└─────────────────────┘
        │
        │  design spec returned
        ▼
┌──────────────────────────────────┐
│  Coder Agent                      │  POST /api/v1/run/coder_flow
│  Input: {student_data + design}   │──────────────────────────────► Langflow
└──────────────────────────────────┘
        │
        │  {index.html, style.css, main.js}
        ▼
┌──────────────────────┐
│  file_writer.py       │  Saves files + creates portfolio_<ts>.zip
└──────────────────────┘
        │
        ▼
   User downloads ZIP
```

### Adding Future Agents (Extensibility)

To add a **Deployer Agent** or any other agent:

1. Create the flow in Langflow and note its Flow ID.
2. Add constants in `config.py`:
   ```python
   DEPLOYER_FLOW_ID = os.getenv("DEPLOYER_FLOW_ID", "")
   DEPLOYER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID = os.getenv("DEPLOYER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID", "")
   ```
3. Add a wrapper function following the same pattern as `call_designer_agent()`.
4. Call the new function from `run_portfolio_generation()` after the coder step.

---

## E. Finding Google Generative AI Component IDs

Each Langflow flow that uses a **Google Generative AI** component requires you to supply
its component ID so the app can send the correct `tweaks` payload.

1. Open the flow in Langflow.
2. Click on the **Google Generative AI** component to select it.
3. A small information box appears — hover over the ID field until it reads **"Click to Copy Full ID"**.
4. Click to copy. The ID looks like `component-123abc`.
5. Paste this value into `config.py` (or the corresponding env var):
   - Designer flow → `DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID`
   - Coder flow    → `CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID`

---

_No Langflow flows are implemented in application code. The Python app only
calls the REST API. All AI logic lives inside Langflow._
