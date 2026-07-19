# Gemini Agent Trace & Replay Dashboard

An LLM agent workflow tracking system built using the **Google GenAI SDK**, **SQLite** for real-time logging, and **Streamlit** for interactive, step-by-step trace analysis.

---

## Project Motive

Autonomous AI agents often behave like "black boxes." When an agent utilizes external tools or enters an execution loop, it becomes incredibly difficult to monitor:
* Exactly what inputs it received at each turn.
* What raw outputs or tool responses were generated.
* How many tokens were consumed per reasoning step.
* When and how the context history was condensed.

This dashboard eliminates the guesswork, providing complete visibility into your agent's inner workings, tool execution loops, and token efficiency.

---

## Key Features

* **Chronological Workflow Tracing:** Tracks steps taken, tools called, inputs provided, and outputs received by the agent in real time.
* **Automatic Chat Condensation:** Automatically reduces the length of the chat history when it exceeds a threshold, saving valuable tokens and reducing prompt payload overhead.
* **Repetition Guarding:** Detects when the model requests an identical tool call (same tool, same arguments) more than once in a run, and blocks re-execution while signaling the model to try a different approach.
* **Token Metrics:** Provides an exact count of input, output, and total tokens used during every single step of the workflow.
* **Highly Extensible Architecture:** Easily add custom tools by defining them in `tool.py` with minimal edits to the core agent logic.
* **Parallel Tool Call Support:** Designed to gracefully handle and log simultaneous, parallel tool executions from the Gemini model.
* **Safety:** I have made sure that AI model can only interact with files inside a folder in the workspace, thus, preventing _Path Traversal attacks_.

---

## Software & Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Language Runtime** | `Python 3.10+` | Core application environment. |
| **LLM Engine** | `Google GenAI SDK` | Powers the agent using the `gemini-2.5-flash` model. |
| **Visualization Layer** | `Streamlit` | Interactive frontend web dashboard framework. |
| **Database Ledger** | `SQLite3` | Engine-native database for zero-config telemetry logging. |
| **Integrated Tools** | `ddgs`, custom math, files | DuckDuckGo web search, sandboxed math evaluator, and workspace manager. |

---

## Architecture

```text
 [ User Prompt ] 
       │
       ▼
 ┌───────────┐       API Calls       ┌──────────────┐
 │ agent5.py │ ────────────────────> │ Gemini LLM   │
 └─────┬─────┘                       └──────┬───────┘
       │                                    │
       │ Handles Parallel Tool Calls        │ Emits Tool Calls &
       │ & Auto-Summarization (>6 turns)    │ Token Usage Telemetry
       ▼                                    ▼
 ┌───────────────┐
 │ agent_log.db  │ <────────────────────────┘
 └──────┬────────┘
        │
        │ Reads Live Logs
        ▼
 ┌───────────────┐
 │  frontend.py  │ ──> [ Streamlit Web UI (Port 8501) ]
 └───────────────┘
 ```

## How to Run

Follow these step-by-step instructions to get the project environment set up and launch the tracking dashboard locally.

### 1. Set Up a Virtual Environment
Navigate to your project folder and run the commands matching your operating system:

* **Step A: Create the environment**
  * *Windows:* `python -m venv venv`
  * *macOS / Linux:* `python3 -m venv venv`

* **Step B: Activate the environment**
  * *Windows (Command Prompt):* `venv\Scripts\activate.bat`
  * *Windows (PowerShell):* `venv\Scripts\Activate.ps1`
  * *macOS / Linux:* `source venv/bin/activate`

* **Step C: Deactivate (when you are done working)**
  * Run `deactivate` on any platform.

### 2. Download the Project & Verify Python
* Download or clone this GitHub repository to your local system.
* Make sure you have a Python interpreter downloaded and configured.

### 3. Install Dependencies
Run the following command to download and install all required Python libraries:
`pip install -r requirements.txt`

### 4. Configure Your API Key
This project uses the Gemini API, which requires a free API key.

* Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
* Set it as an environment variable named `GEMINI_API_KEY`:
  * *Windows (Command Prompt):* `set GEMINI_API_KEY=your_key_here`
  * *Windows (PowerShell):* `$env:GEMINI_API_KEY="your_key_here"`
  * *macOS / Linux:* `export GEMINI_API_KEY=your_key_here`

### 5. Run the Agent
Open `agent5.py` and edit the prompt inside the `if __name__ == "__main__":` block at the bottom of the file to whatever task you want the agent to attempt. Then run: `python agent5.py`
This executes the agent loop and logs every step (tool calls, arguments, outputs, token usage, and summarization events) to `agent_log.db`. Any files that the agent creates or reads will be in my_project_agent_files folder only.

### 6. View the Trace Dashboard
In a separate terminal (with the virtual environment activated), run: `streamlit run frontend.py`
Open the local URL shown in your terminal (default: `http://localhost:8501`) to inspect the run step-by-step, including tool inputs/outputs, condensation events, and token usage per step.

 ## Limitations/Known Issues
 * **Noisy search results:** The web search result generally contains a huge link which is of no use to the AI agent in forming an answer. Sometimes it only contains unnecessary details and not the actual correct answer. This can be clearly seen for the prompts like-`"Who is the Prime Minister of India?"`
 * **Fixed summarizations threshold:** The chat history currently summarizes if the length of chats exceeds 6. This value is hardcoded for testing and would need to be tuned in production — too low, and long conversations get summarized so often that earlier computed details risk being diluted; too high, and token usage grows unnecessarily before any condensation happens. This shows a tradeoff between summarizing the chat frequently and the quality of answers. We can set the summarization to occur based on chat history token count instead of prompt count.