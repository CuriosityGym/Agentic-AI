# 🚀 Agentic AI Course: Building Intelligent Agents

Welcome to the **Agentic AI Course**! This repository is your hands-on laboratory for building and deploying Agentic AI. You will learn to orchestrate logic using **Langflow** and create interactive front-ends using **Gradio**.

---

## 📚 Course Overview
This course is structured into 5 sections. The first section covers environment setup, while the remaining 4 sections focus on building the following agents:

1.  **Agent 1: Exam Strategy Agent** – An AI tutor that analyzes uploaded exams, provides feedback on student answers, and explains complex concepts.
2.  **Agent 2: YouTube Video Summary Generator** – Converts long YouTube videos into short, actionable summaries to save study time.
3.  **Agent 3: Smart Homework Planner** – Predicts the best study blocks by reading your calendar and assignment deadlines.
4.  **Agent 4: Personal Portfolio Website Agent** – A developer agent that crafts a unique portfolio website based on your skills and interests.

---

## 📋 Pre-requisites
* **MySphere Account:** Ensure you are logged in at [mysphere.net](https://mysphere.net).
* **GitHub Account:** To fork this repo and run the environment.
* **Google Gemini API Key:** Required for the AI components within Langflow.

---

## 🛠️ Phase 1: Initial Environment Setup
*Perform these steps once to get started.*

1.  **Fork the Repository:** Click the **Fork** button at the top right of this page.
2.  **Launch GitHub Codespaces:**
    * Go to [github.com/codespaces](https://github.com/codespaces).
    * Select your fork and choose the **2-core CPU / 8GB RAM** environment.
    * Click **Create codespace** and wait for the editor to load.

---

## 🤖 Phase 2: Running the AI Infrastructure (Langflow)
This starts the backend engine that manages your Agentic Flows.

1.  **Start Langflow:** Run the following command in the terminal:
    ```bash
    docker compose up -d
    ```
2.  **Make Langflow Public:**
    * Open the **Ports** tab in the terminal area.
    * Find **Port 7860**.
    * Right-click the "Visibility" column and select **Make Public**.
    * *VS Code may notify you of a running application; you can ignore or close this notification.*

---

## 🖱️ Phase 3: Running an Agent Example
*You will repeat these steps for each of the 4 agents in the course.*

1.  **Navigate to the Agent Folder:**
    ```bash
    cd [folder-name]
    # Example: cd exam-strategy-agent
    ```
2.  **Create Python Environment, Activate Python Environment & Install Packages:**
    ```bash
    python3 -m venv my_env
    source my_env/bin/activate
    pip install -r requirements.txt
    ```
3.  **Launch the Gradio UI:**
    ```bash
    python3 app.py or python3 app_chat.py
    ```
4.  **Get the Public URLs:**
    * **Langflow URL:** Copy the Public URL for Port **7860** from the Ports tab.
    * **Gradio URL:** Gradio has `share=true` enabled, so it will generate a `https://...gradio.live` link in the terminal. **Use this .live link for registration.**

---

## 🔗 Phase 4: Connecting & Registering
To link your local code to the MySphere course platform:

1.  **Configure IDs:** Open the Langflow UI (Port 7860) and retrieve your **Flow ID**, **Langflow API Key**, and **Google Generative AI Component ID**.
2.  **Register the Codespace:** Click the link below to open the registration form:
    👉 [Register your Codespace (Course ID: 442)](https://mysphere.net/register-codespace?courseId=442)
3.  **Submit URLs:** Paste your **Public Gradio URL** and **Public Langflow URL** into the form and click **Register**.
4.  **Success:** Once registered, you can interact with your agent!

---

## ⌨️ Terminal Command Reference

| Command | Explanation |
| :--- | :--- |
| `docker compose up -d` | Runs the Langflow container in the background (detached mode). |
| `pip install -r requirements.txt` | Downloads and installs all Python libraries needed for the agent. |
| `python3 app.py` | Executes the Python script to launch the Gradio User Interface. |
| `source env_name/bin/activate` | Switches the terminal to use the specific Python environment for that folder. |

> [!IMPORTANT]
> **Switching Agents:** To move to a different example, stop the current process (**Ctrl + C**), use `cd ..` to return to the root directory, navigate to the next agent folder, and repeat **Phase 3 & 4**.
