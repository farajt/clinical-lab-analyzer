import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.schemas import AnalyzeRequest, AnalyzeResponse, ExplainedResult
from app.agent import get_agent

load_dotenv()

app = FastAPI(title="Clinical Lab Results Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze_labs", response_model=AnalyzeResponse)
async def analyze_labs(request: AnalyzeRequest):
    if not request.labs:
        raise HTTPException(status_code=400, detail="No lab results provided")

    agent = get_agent()
    initial_state = {"labs": [lab.model_dump() for lab in request.labs]}

    try:
        final_state = await agent.ainvoke(initial_state)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {type(e).__name__}: {e}"
        )

    explained = final_state["explained"]

    def to_results(bucket):
        out = []
        for item in explained.get(bucket, []):
            out.append(
                ExplainedResult(
                    test_name=item.get("test_name", "unknown"),
                    value=item.get("value", 0.0) or 0.0,
                    unit=item.get("unit") or "",
                    status=item.get("status", "Unknown"),
                    normal_range=item.get("normal_range"),
                    explanation=item.get("explanation", ""),
                    next_steps=item.get("next_steps", []),
                    error=item.get("error"),
                )
            )
        return out

    return AnalyzeResponse(
        patient_id=request.patient_id,
        critical=to_results("critical"),
        warning=to_results("warning"),
        normal=to_results("normal"),
        unresolved=to_results("unresolved"),
    )