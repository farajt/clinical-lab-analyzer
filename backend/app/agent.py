"""
LangGraph agent with three nodes, run in sequence:

classify
    - for each lab, try numeric classification first (via the MCP
      server's classify_value tool).
    - If the value truly isn't a number, fall back to qualitative
      strip-test interpretation (Normal/Negative/1+/etc).
    - Only if neither applies is the result marked unresolved.

route
    - group classified results into critical / warning / normal / unresolved

explain
    - for every classifiable result, ask the LLM for a plain-English
      clinical explanation + suggested next steps.

State flows through the graph as a TypedDict; each node only touches
its own keys, which keeps them independently testable.
"""

from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from app.mcp_client import call_classify_value
from app.llm import get_llm


class AgentState(TypedDict):
    labs: List[Dict[str, Any]]
    classified: List[Dict[str, Any]]
    routed: Dict[str, List[Dict[str, Any]]]
    explained: Dict[str, List[Dict[str, Any]]]


class ExplanationOutput(BaseModel):
    explanation: str = Field(
        description=(
            "2-3 sentence clinically relevant explanation of WHY this "
            "result is flagged and what it means, in plain but accurate "
            "language a patient or nurse could follow"
        )
    )

    next_steps: List[str] = Field(
        description=(
            "1-3 concrete, actionable next steps. For Normal results, "
            "one line of reassurance/routine follow-up is enough"
        )
    )


QUALITATIVE_NORMAL = {
    "normal",
    "negative",
    "negatif",
}

QUALITATIVE_WARNING = {
    "1+",
    "2+",
    "3+",
    "4+",
    "positive",
    "pozitif",
}


# ---------- Node 1: Classify ----------

async def classify_node(state: AgentState) -> AgentState:
    classified = []

    for lab in state["labs"]:
        test_name = lab.get("test_name", "")
        value = lab.get("value")

        is_strip_test = "(strip)" in test_name.lower()

        # Missing value
        if value is None:
            classified.append({
                **lab,
                "status": "Error",
                "error": "missing value",
            })
            continue

        # ---------------------------------------------------------
        # FIRST: Try numeric classification for EVERY test.
        #
        # This is important because some strip tests are numeric,
        # e.g.:
        #   pH (Strip)       = 6
        #   Dansite (Strip)  = 1.02
        #
        # These must use their numeric reference ranges through MCP.
        # ---------------------------------------------------------

        numeric_value = None

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = None

        if numeric_value is not None:
            result = await call_classify_value(
                test_name,
                numeric_value,
                lab.get("min_reference"),
                lab.get("max_reference"),
            )

            if result.get("status") == "Unknown":
                classified.append({
                    **lab,
                    "value": numeric_value,
                    "status": "Unknown",
                    "error": result.get("reason"),
                })
            else:
                classified.append({
                    **lab,
                    "value": numeric_value,
                    **result,
                })

            continue

        # ---------------------------------------------------------
        # SECOND: Qualitative strip-test classification.
        #
        # Examples:
        #   Protein (Strip)   = Negatif  -> Normal
        #   Nitrit (Strip)    = Negatif  -> Normal
        #   Eritrosit (Strip) = 1+       -> Warning
        # ---------------------------------------------------------

        if is_strip_test:
            qualitative_value = str(value).strip().lower()

            if qualitative_value in QUALITATIVE_NORMAL:
                classified.append({
                    **lab,
                    "status": "Normal",
                    "normal_range": None,
                    "range_source": "qualitative",
                })
                continue

            if qualitative_value in QUALITATIVE_WARNING:
                classified.append({
                    **lab,
                    "status": "Warning",
                    "normal_range": None,
                    "range_source": "qualitative",
                })
                continue

            classified.append({
                **lab,
                "status": "Unknown",
                "normal_range": None,
                "error": (
                    f"unrecognized qualitative result "
                    f"('{value}') for '{test_name}'"
                ),
            })

            continue

        # ---------------------------------------------------------
        # THIRD: Non-numeric non-strip value.
        # ---------------------------------------------------------

        classified.append({
            **lab,
            "status": "Error",
            "error": (
                f"qualitative/non-numeric result ('{value}') — "
                "automatic classification only supports numeric labs"
            ),
        })

    return {
        **state,
        "classified": classified,
    }


# ---------- Node 2: Route ----------

def route_node(state: AgentState) -> AgentState:
    routed = {
        "critical": [],
        "warning": [],
        "normal": [],
        "unresolved": [],
    }

    for item in state["classified"]:
        status = item.get("status")

        if status == "Critical":
            routed["critical"].append(item)

        elif status == "Warning":
            routed["warning"].append(item)

        elif status == "Normal":
            routed["normal"].append(item)

        else:
            routed["unresolved"].append(item)

    return {
        **state,
        "routed": routed,
    }


# ---------- Node 3: Explain ----------

async def explain_node(state: AgentState) -> AgentState:
    llm = get_llm()

    structured_llm = llm.with_structured_output(
        ExplanationOutput
    )

    explained = {
        "critical": [],
        "warning": [],
        "normal": [],
        "unresolved": [],
    }

    for bucket, items in state["routed"].items():

        for item in items:

            # Unresolved results don't get a misleading clinical
            # explanation because classification itself failed.
            if bucket == "unresolved":
                explained[bucket].append({
                    **item,
                    "explanation": (
                        f"Could not classify: "
                        f"{item.get('error', 'unknown issue')}"
                    ),
                    "next_steps": [
                        "Verify test name and value; "
                        "re-enter or check with lab."
                    ],
                })

                continue

            prompt = (
                f"Lab test: {item.get('test_name')}\n"
                f"Value: {item.get('value')} "
                f"{item.get('unit', '')}\n"
                f"Normal range: {item.get('normal_range')}\n"
                f"Status: {item.get('status')}\n\n"

                "Explain this result for a clinician-facing dashboard "
                "using Explainable AI principles. Be specific about "
                "WHY this value triggered this status, referencing "
                "the number/value and the range or qualitative "
                "interpretation when applicable, not just "
                "'abnormal'."
            )

            try:
                result: ExplanationOutput = await structured_llm.ainvoke(
                    prompt
                )

                explained[bucket].append({
                    **item,
                    "explanation": result.explanation,
                    "next_steps": result.next_steps,
                })

            except Exception as e:
                explained[bucket].append({
                    **item,
                    "explanation": (
                        f"Explanation unavailable "
                        f"(LLM error: {e})."
                    ),
                    "next_steps": [
                        "Retry analysis; consult clinician if urgent."
                    ],
                })

    return {
        **state,
        "explained": explained,
    }


# ---------- Build LangGraph ----------

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify", classify_node)
    graph.add_node("route", route_node)
    graph.add_node("explain", explain_node)

    graph.set_entry_point("classify")

    graph.add_edge("classify", "route")
    graph.add_edge("route", "explain")
    graph.add_edge("explain", END)

    return graph.compile()


_compiled_graph = None


def get_agent():
    global _compiled_graph

    if _compiled_graph is None:
        _compiled_graph = build_graph()

    return _compiled_graph