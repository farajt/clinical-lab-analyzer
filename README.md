# Clinical Lab Results Analyzer

A full-stack tool that takes lab test results and tells you not just whether
something is abnormal, but why. Every flagged result is compared against a
reference range and explained in plain clinical language, with suggested
next steps — built around the idea that clinicians should be able to see
the reasoning behind a classification, not just a red or yellow label.

## How it works

```
React (Vite)              FastAPI                 MCP Server            Groq
LabInput.jsx   --POST-->  /analyze_labs  -------->  reference lookup
ResultsDisplay.jsx          |                        classify_value    LLM explanation
SeverityBadge.jsx      LangGraph agent          (real MCP protocol,   (structured output,
                    classify -> route -> explain   over stdio)         called per result)
```

The agent is a three-node LangGraph pipeline:

- **classify** — for every lab result, calls the MCP server's
  `classify_value` tool over the actual MCP protocol (not a plain function
  call) to compare the value against a reference range and assign
  Normal / Warning / Critical. Handles three kinds of messy input without
  crashing: missing values, unknown test names, and non-numeric results.
- **route** — groups results into critical / warning / normal / unresolved,
  critical first.
- **explain** — calls the LLM once per result (even for Normal ones) to
  produce a short, specific explanation and 1–3 next steps.

Reference ranges come from two places. If the input row already states its
own range (like the Kaggle dataset does, via `Min_Reference`/`Max_Reference`
columns), the MCP tool uses that directly. If not, it falls back to a
hardcoded dictionary of ~12 common tests. A critical band is derived as 50%
of the normal range's width beyond each edge, so a result has to be clearly
outside normal — not just barely over — to get flagged Critical instead of
Warning.

Some lab tests aren't numbers at all — urine dipstick results like
"Negatif" or "1+". These are handled separately: the classifier tries a
numeric parse first, and only falls back to qualitative interpretation
(Normal/Negative → Normal, 1+/2+/Positive → Warning) if the value genuinely
isn't a number.

## AI provider

Groq, via `langchain-groq`, using `openai/gpt-oss-20b`. Groq's free tier is
generous and fast enough that explanations come back in a second or two.
Ollama is supported as a fully local fallback with no API key — switching
providers is one line in `.env` (`LLM_PROVIDER=ollama`), no code changes.

## Data source

Built against the Kaggle dataset *Laboratory Test Results – Anonymized
Dataset*. It's been tested end-to-end with a real 27-row export from that
dataset — including Turkish test names, dataset-provided reference ranges,
and both qualitative and numeric urine strip results. Result: 26 Normal,
1 Warning (a positive erythrocyte strip test, correctly flagged), 0
unresolved.

The `/test_data` folder also has three smaller synthetic CSVs
(`normal_results.csv`, `warning_results.csv`, `critical_results.csv`) for
quickly exercising each severity tier without needing a Kaggle account.

## Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here       # free at console.groq.com
GROQ_MODEL=openai/gpt-oss-20b
```

Then run it:

```bash
uvicorn app.main:app --reload --port 8000
```

Check `http://localhost:8000/health` — should return `{"status":"ok"}`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env    # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open the local URL Vite prints (usually `http://localhost:5173`).

### Using Ollama instead of Groq

```bash
ollama pull llama3.1
```

Then in `backend/.env`, set `LLM_PROVIDER=ollama`.

## A note on Windows

Spawning the MCP server as a subprocess requires the Proactor event loop,
which uvicorn doesn't reliably use on Windows, especially with `--reload`.
`mcp_client.py` works around this by running MCP calls on a dedicated
background thread with its own event loop, so this works the same on
Windows, Mac, and Linux without any platform-specific setup on your end.

## Testing

1. Start both servers as above.
2. Upload any file in `/test_data`, or a CSV exported from the Kaggle
   dataset, via the "Upload CSV" tab.
3. Or use "Manual entry" to type in individual results.
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
  mcp_server.py        MCP server: reference_range_lookup, classify_value tools
  mcp_client.py         MCP client (background-thread event loop, Windows-safe)
  reference_data.py      Hardcoded fallback reference ranges
  llm.py                  Groq/Ollama provider switch
  schemas.py                Pydantic request/response models
frontend/src/
  App.jsx
  api.js
  components/LabInput.jsx, ResultsDisplay.jsx, SeverityBadge.jsx
test_data/                  3 synthetic CSVs + a sample from the real Kaggle dataset
```

## Known limitations

- The hardcoded reference-range dictionary covers common tests only;
  anything outside it needs a dataset row that supplies its own
  `min_reference`/`max_reference`, or it's routed to "unresolved" rather
  than guessed at.
- The MCP server is spawned fresh per request rather than kept as a
  long-lived session — simpler to reason about, at some cost to latency.
- Qualitative strip-test interpretation only recognizes a small set of
  standard phrases (Normal/Negative/1+ through 4+/Positive); anything else
  is reported as unresolved rather than misclassified.
