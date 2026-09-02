"""
Talks to app/mcp_server.py (spawned as a subprocess) over stdio using the
MCP protocol.

Windows note: spawning a subprocess requires the Proactor event loop, but
uvicorn's main loop (especially under --reload) doesn't reliably use it.

So instead of running on uvicorn's loop, we run a single dedicated
background thread with its own event loop (Proactor on Windows) just for
MCP calls, and bridge to it with run_coroutine_threadsafe.

This works the same way on Mac/Linux too, just unnecessary there.
"""

import asyncio
import json
import sys
import threading
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "app.mcp_server"],
)


_loop: asyncio.AbstractEventLoop | None = None
_loop_ready = threading.Event()


def _run_background_loop():
    global _loop

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsProactorEventLoopPolicy()
        )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    _loop = loop
    _loop_ready.set()

    loop.run_forever()


def _get_loop() -> asyncio.AbstractEventLoop:
    if not _loop_ready.is_set():
        t = threading.Thread(
            target=_run_background_loop,
            daemon=True,
            name="mcp-loop",
        )
        t.start()

        _loop_ready.wait()

    return _loop


@asynccontextmanager
async def mcp_session():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def _reference_range_lookup_impl(test_name: str) -> dict:
    async with mcp_session() as session:
        result = await session.call_tool(
            "reference_range_lookup",
            {"test_name": test_name},
        )

        return json.loads(result.content[0].text)


async def _classify_value_impl(
    test_name: str,
    value: float,
    min_reference: float | None = None,
    max_reference: float | None = None,
) -> dict:
    async with mcp_session() as session:
        result = await session.call_tool(
            "classify_value",
            {
                "test_name": test_name,
                "value": value,
                "min_reference": min_reference,
                "max_reference": max_reference,
            },
        )

        return json.loads(result.content[0].text)


async def _run_on_bg_loop(coro):
    loop = _get_loop()

    fut = asyncio.run_coroutine_threadsafe(coro, loop)

    return await asyncio.wrap_future(fut)


async def call_reference_range_lookup(test_name: str) -> dict:
    return await _run_on_bg_loop(
        _reference_range_lookup_impl(test_name)
    )


async def call_classify_value(
    test_name: str,
    value: float,
    min_reference: float | None = None,
    max_reference: float | None = None,
) -> dict:
    return await _run_on_bg_loop(
        _classify_value_impl(
            test_name,
            value,
            min_reference,
            max_reference,
        )
    )