"""Live test: sends a real prompt through the Agent SDK (costs money).

Skipped unless you pass --run-live:  uv run pytest --run-live
"""

import pytest
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

pytestmark = [pytest.mark.live, pytest.mark.anyio]


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_real_query_returns_expected_text():
    options = ClaudeAgentOptions(
        model="claude-opus-5-5",
        tools=[],  # no built-in tools: smaller prompt, nothing touches the disk
        max_turns=1,
        effort="low",
        max_budget_usd=1.0,  # hard stop if something goes wrong
    )

    result = None
    async for message in query(prompt="Reply with exactly: SDK OK", options=options):
        if isinstance(message, ResultMessage):
            result = message

    assert result is not None, "no ResultMessage received"
    assert not result.is_error, f"{result.subtype}: {result.errors}"
    assert result.subtype == "success"
    assert "SDK OK" in (result.result or "")
