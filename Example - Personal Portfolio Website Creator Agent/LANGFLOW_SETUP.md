# Langflow Flow Setup Guide

This document explains how to create and connect the two AI agent flows
required by the **Personal Portfolio Website Builder Agent** inside Langflow.

---

## A. How to Create the Designer Flow in Langflow

1. Open Langflow at your registered Github Codespace URL.
2. Click **New Flow → Blank Flow**.
3. Name it `Designer Flow` and save.
4. Copy the auto-generated **Flow ID** (visible in the URL or flow settings).
   Update `DESIGNER_FLOW_ID` in `config.py` if it differs.
5. Find the **Google Generative AI component ID** and set
   `DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID` in `config.py`.
   (See [Section E](#e-finding-google-generative-ai-component-ids) for instructions.)

### Designer Flow Architecture

```
[Student Data JSON]
         │
         ▼
┌────────────────┐
│  Chat Input    │  Receives stringified student_data JSON
└────────────────┘
         │
         ▼
┌──────────────────────┐
│  Prompt Template     │  System prompt: design specification instructions
└──────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Google Generative AI  │  gemini-2.5-flash  ·  2000 tokens  ·  temp 0.20
└────────────────────────┘
         │
         ▼
┌────────────────┐
│  Chat Output   │  Returns design spec JSON to the Python app
└────────────────┘
```

---

## B. How to Create the Coder Flow in Langflow

1. Open Langflow at your registered Github Codespace URL.
2. Click **New Flow → Blank Flow**.
3. Name it `Coder Flow` and save.
4. Copy the auto-generated **Flow ID** and set `CODER_FLOW_ID` in `config.py` accordingly.
5. Find the **Google Generative AI component ID** and set
   `CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID` in `config.py`.
   (See [Section E](#e-finding-google-generative-ai-component-ids) for instructions.)

### Coder Flow Architecture

```
[Student Data + Design Spec JSON]
         │
         ▼
┌────────────────┐
│  Chat Input    │  Receives stringified {"student_data": {...}, "design": {...}}
└────────────────┘
         │
         ▼
┌──────────────────────┐
│  Prompt Template     │  System prompt: web development instructions
└──────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Google Generative AI  │  gemini-2.5-flash  ·  16000 tokens  ·  temp 0.20
└────────────────────────┘
         │
         ▼
┌────────────────┐
│  Chat Output   │  Returns {"index.html", "style.css", "main.js"} to the Python app
└────────────────┘
```

---

## C. Required Components in Each Flow

### Designer Flow Components

| Component | Role |
|-----------|------|
| **Chat Input** | Receives the stringified `student_data` JSON (all 10 fields) |
| **Prompt Template** | System prompt instructing the model to produce a design JSON |
| **Google Generative AI** | Language model that generates the design specification |
| **Chat Output** | Returns the design spec JSON to the Python app |

#### Prompt Template Text

Paste the following into the **Template** field of the Prompt Template component:

```
You are an expert portfolio website designer. Based on the student data below,
produce a JSON design specification.

The student data contains: name, school, grade, introduction, links, hobbies,
interests, skills, courses, projects, and theme_preference.

Produce a JSON design spec with exactly these keys:
  "theme"    – one of: "dark", "light", "colorful", "minimal".
               If the student provided a theme_preference, honour it.
  "layout"   – one of: "standard", "modern", "creative", "minimal"
  "sections" – JSON array of page sections to include, chosen from:
               "about", "projects", "skills", "courses", "hobbies", "interests", "contact"
               Only include a section if the matching student_data field is non-empty.

Student data:
{input_value}

Respond ONLY with valid JSON. No markdown, no explanation.
```

#### Recommended Model Settings

| Setting | Value |
|---------|-------|
| **Model** | `gemini-2.5-flash` |
| **Max Output Tokens** | `2000` |
| **Temperature** | `0.20` |

> **Why low temperature?** The Designer Agent must return strictly valid JSON with a
> fixed schema. A low temperature reduces format errors and hallucinated keys.

---

### Coder Flow Components

| Component | Role |
|-----------|------|
| **Chat Input** | Receives stringified `{"student_data": {...}, "design": {...}}` |
| **Prompt Template** | System prompt instructing the model to write HTML / CSS / JS |
| **Google Generative AI** | Language model that generates the website source code |
| **Chat Output** | Returns `{"index.html": "...", "style.css": "...", "main.js": "..."}` to the Python app |

#### Prompt Template Text

Paste the following into the **Template** field of the Prompt Template component:

```
You are an expert web developer. Using the student data and design specification
below, generate a complete personal portfolio website.

Return ONLY valid JSON with exactly these three keys:
  "index.html"  – full HTML document (no external CDN dependencies)
  "style.css"   – all CSS styles
  "main.js"     – all JavaScript

The portfolio must render all non-empty fields from student_data:
  name, school, grade, introduction, links (social / website links),
  hobbies, interests, skills, courses, and projects.
Use the design spec to determine the theme, layout, and which sections to include.

Input:
{input_value}

Respond ONLY with valid JSON. No markdown, no explanation.
```

#### Recommended Model Settings

| Setting | Value |
|---------|-------|
| **Model** | `gemini-2.5-flash` |
| **Max Output Tokens** | `16000` |
| **Temperature** | `0.20` |

> **Why high max tokens?** The Coder Agent generates three complete files
> (HTML + CSS + JS). A full portfolio page with inline styles and scripts can
> easily exceed 8 000 tokens, so a generous limit prevents truncated output.

---

### Student Data Schema

Both flows receive `student_data`. Below is the complete schema (from `schema.py`):

```json
{
  "name":             "Alice Smith",
  "school":           "Riverside High",
  "grade":            "10",
  "introduction":     "I'm a passionate student who loves coding and art.",
  "links": [
    { "name": "Github",    "url": "https://github.com/alice" },
    { "name": "LinkedIn",  "url": "https://linkedin.com/in/alice" }
  ],
  "hobbies":          ["Reading", "Coding", "Hiking"],
  "interests":        ["Artificial Intelligence", "Music Production"],
  "skills":           ["Python", "HTML", "CSS"],
  "courses":          ["Computer Science", "AP Mathematics"],
  "projects": [
    { "name": "Weather App", "description": "React app showing live weather", "file_path": "" }
  ],
  "theme_preference": "dark"
}
```

The Designer Agent receives `student_data` directly.
The Coder Agent receives `{ "student_data": <above>, "design": <designer output> }`.

---

## D. How to Connect the Flows via API

### Environment Variables

Set in your shell or a `.env` file before running `app.py`:

```bash
export LANGFLOW_BASE_URL="https://api.mysphere.net"                            # Do not change this URL
export LANGFLOW_TOKEN="your-langflow-api-token"                                # From Langflow → Settings → API Keys
export DESIGNER_FLOW_ID="your-designer-flow-id"
export DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID="component-xxxxxx"         # See Section E
export CODER_FLOW_ID="your-coder-flow-id"
export CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID="component-xxxxxx"            # See Section E
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
  "session_id":  "<unique-session-id>",
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

### Flow Execution Order (handled automatically by `coder.py`)

```
[Student Data Collected via Chat UI]
         │
         │  Step 1 — designer_flow
         ▼
┌──────────────────────────────────┐
│  Designer Agent                  │  Input: student_data (JSON)
│  POST /api/v1/proxy/langflow/run │──► Langflow
│        /{DESIGNER_FLOW_ID}       │◄── returns design spec JSON
└──────────────────────────────────┘
         │
         │  Step 2 — coder_flow  (retried once if output is incomplete)
         ▼
┌──────────────────────────────────┐
│  Coder Agent                     │  Input: {student_data, design}
│  POST /api/v1/proxy/langflow/run │──► Langflow
│        /{CODER_FLOW_ID}          │◄── returns {index.html, style.css, main.js}
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────┐
│  file_writer.py      │  Saves files to outputs/portfolio_<timestamp>/
└──────────────────────┘
         │
         ▼
   User downloads the generated portfolio files
```

---

## E. Finding Google Generative AI Component IDs

Each Langflow flow that uses a **Google Generative AI** component requires you to supply
its component ID so the app can send the correct `tweaks` payload.

1. Open the flow in Langflow.
2. Click on the **Google Generative AI** component to select it.
3. A small information box appears — hover over the ID field until it reads
   **"Click to Copy Full ID"**.
4. Click to copy. The ID looks like `component-123abc`.
5. Paste this value into `config.py` (or the corresponding env var):
   - Designer flow → `DESIGNER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID`
   - Coder flow    → `CODER_FLOW_TWEAKS_API_GOOGLE_COMPONENT_ID`

---

*No AI logic is hard-coded in the Python application. All LLM calls go through
Langflow. To swap the model, adjust the output format, or refine the prompt,
update the relevant flow in Langflow — no Python changes required.*