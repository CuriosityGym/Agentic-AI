# Langflow Flow Setup Guide

This document explains how to create and connect the two AI agent flows
required by the **Personal Portfolio Website Builder** inside Langflow.

---

## A. How to Create the Designer Flow in Langflow

1. Open Langflow at `http://localhost:7860`.
2. Click **New Flow → Blank Flow**.
3. Name it `designer_flow` and save.
4. Copy the auto-generated **Flow ID** (visible in the URL or flow settings).
   Update `DESIGNER_FLOW_ID` in `services/langflow_client.py` if it differs.

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

1. Open Langflow at `http://localhost:7860`.
2. Click **New Flow → Blank Flow**.
3. Name it `coder_flow` and save.
4. Copy the auto-generated **Flow ID** and set `CODER_FLOW_ID` accordingly.

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
| **OpenAI / Anthropic LLM** | Language model that generates the design spec |
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
| **OpenAI / Anthropic LLM** | Language model that generates the website code |
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
# Optional: only required if Langflow has authentication enabled
export LANGFLOW_TOKEN="your-langflow-api-token"

# Optional: override the default base URL
export LANGFLOW_BASE_URL="http://localhost:7860"
```

### Obtaining a Langflow API Token

1. In Langflow, go to **Settings → API Keys**.
2. Create a new key and copy the token.
3. Set it as `LANGFLOW_TOKEN` (see above).

### API Call Structure

The Python client (`services/langflow_client.py`) POSTs to:

```
POST http://localhost:7860/api/v1/run/{flow_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "input_value": "<stringified JSON payload>"
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
2. Add a constant in `services/langflow_client.py`:
   ```python
   DEPLOYER_FLOW_ID = "deployer_flow"
   ```
3. Add a wrapper function following the same pattern as `call_designer_agent()`.
4. Call the new function from `run_portfolio_generation()` after the coder step.

---

_No Langflow flows are implemented in application code. The Python app only
calls the REST API. All AI logic lives inside Langflow._
