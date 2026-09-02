"""
MCP server: exposes lab-domain tools over the Model Context Protocol.
The LangGraph agent talks to this server (not to plain Python functions)
for reference-range lookups and classification. Run standalone or spawned
via stdio by mcp_client.py.
"""

from mcp.server.fastmcp import FastMCP
from app.reference_data import REFERENCE_RANGES, normalize_test_name

mcp = FastMCP("lab-analyzer-tools")


@mcp.tool()
def reference_range_lookup(test_name: str) -> dict:
    """
    Look up the normal/critical reference range for a lab test.
    Returns unit, normal low/high, and critical low/high.
    If the test isn't in the hardcoded dict, returns found=False.
    """
    key = normalize_test_name(test_name)
    entry = REFERENCE_RANGES.get(key)

    if not entry:
        return {"found": False, "test_name": test_name}

    return {"found": True, "test_name": key, **entry}


@mcp.tool()
def classify_value(
    test_name: str,
    value: float,
    min_reference: float | None = None,
    max_reference: float | None = None,
) -> dict:
    """
    Classify a value as Normal/Warning/Critical.

    Uses min_reference/max_reference directly if given
    (e.g. from a dataset row that states its own range),
    otherwise falls back to the hardcoded dict.
    """

    if min_reference is not None and max_reference is not None:
        low, high = float(min_reference), float(max_reference)

        width = high - low

        if width <= 0:
            width = max(abs(high), 1.0) * 0.1

        critical_low = low - 0.5 * width
        critical_high = high + 0.5 * width

        range_source = "dataset"

    else:
        key = normalize_test_name(test_name)
        entry = REFERENCE_RANGES.get(key)

        if not entry:
            return {
                "status": "Unknown",
                "reason": f"No reference range for '{test_name}'",
            }

        low, high = entry["low"], entry["high"]
        critical_low = entry["critical_low"]
        critical_high = entry["critical_high"]

        range_source = "hardcoded"

    if (
        critical_low <= value < low
        or high < value <= critical_high
    ):
        status = "Warning"

    elif value < critical_low or value > critical_high:
        status = "Critical"

    else:
        status = "Normal"

    return {
        "status": status,
        "value": value,
        "normal_range": [low, high],
        "critical_band": [critical_low, critical_high],
        "range_source": range_source,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")