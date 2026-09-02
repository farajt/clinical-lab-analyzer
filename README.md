# Clinical Lab Results Analyzer

A full-stack app that takes lab test results, classifies them **Normal / Warning / Critical**
against reference ranges, and uses an LLM to explain *why* — not just label them — plus suggests
next steps. Built around Explainable AI: every flagged result shows the number, the range, and the
reasoning behind the status.

## Architecture

```
React (Vite)                FastAPI                    MCP Server              Groq / Ollama
LabInput.jsx  ──POST──►  /analyze_labs  ──LangGraph──►  reference_range_lookup
ResultsDisplay.jsx                        agent            classify_value        LLM explanation
SeverityBadge.jsx                     (classify→route→explain)                  (structured output)
```

- **Agent (LangGraph)**: three sequential nodes.
  - `classify` — for each lab result, calls the **MCP server's** `classify_value` tool (real
    MCP protocol over stdio, not a plain function call) to compare the value against reference
    ranges and assign Normal/Warning/Critical. Handles missing values, non-numeric values, and
    unknown test names without crashing.
  - `route` — groups results into `critical` / `warning` / `normal` / `unresolved` buckets,
    critical-first.
  - `explain` — calls the LLM (via LangChain, structured output) for every result to generate a
    plain-language clinical explanation and next steps.
- **MCP server** (`app/mcp_server.py`) exposes `reference_range_lookup` and `classify_value` as
  MCP tools. The agent never touches the reference-range dict directly — it always goes through
  the MCP client (`app/mcp_client.py`).
- **Frontend**: manual form entry or CSV upload → POST to `/analyze_labs` → results rendered
  grouped by severity with color-coded badges, explanations, and next steps.

## AI Provider

**Groq** (`llama-3.1-8b-instant`) by default — fast, generous free tier, drop-in via
`langchain-groq`. **Ollama** is supported as a fully local, no-API-key fallback — switch with one
env var (`LLM_PROVIDER=ollama`), no code changes.

## Setup

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set GROQ_API_KEY (get a free key at console.groq.com)
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000, edit if needed
npm run dev
```
Open the printed local URL (default `http://localhost:5173`).

### Using Ollama instead of Groq
```bash
ollama pull llama3.1
# in backend/.env: LLM_PROVIDER=ollama
```

## How to test

1. Start both servers (above).
2. In the UI, switch to **Upload CSV** and pick a file from `/test_data`:
   - `normal_results.csv` — all results in range
   - `warning_results.csv` — mildly abnormal results
   - `critical_results.csv` — severe results, plus an unknown test name and a missing value
     (exercises error handling)
3. Or use **Manual entry** to type in individual results.
4. Or hit the API directly:
   ```bash
   curl -X POST http://localhost:8000/analyze_labs \
     -H "Content-Type: application/json" \
     -d '{"labs": [{"test_name": "hemoglobin", "value": 6.5, "unit": "g/dL"}]}'
   ```

## Project structure
```
backend/app/
  main.py              FastAPI app, /analyze_labs endpoint
  agent.py             LangGraph agent (classify -> route -> explain)
  mcp_server.py         MCP server: reference_range_lookup, classify_value tools
  mcp_client.py          MCP client used by the agent
  reference_data.py      Hardcoded reference ranges
  llm.py                  Groq/Ollama provider switch
  schemas.py               Pydantic request/response models
frontend/src/
  App.jsx
  api.js
  components/LabInput.jsx, ResultsDisplay.jsx, SeverityBadge.jsx
test_data/                 3 synthetic CSVs
```

## Known limitations
- Reference range dict covers 12 common tests; unknown tests are routed to "unresolved" rather
  than guessed at.
- MCP server is spawned per-request via stdio for simplicity; a production build would keep a
  persistent MCP session.
