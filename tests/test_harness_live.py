"""Live tests: agy-harness controlling a real Claude agent (costs money).

Skipped unless you pass --run-live:  uv run pytest --run-live
"""

import pytest
from agy_harness.core.state import HarnessState
from agy_harness.core.types import BudgetSpec, ContractSpec
from agy_harness.graph.node import LLMNode
from agy_harness.graph.state_graph import StateGraph
from agy_harness.integrations.claude_sdk import ClaudeHarness, claude_provider
from agy_harness.loop.engine import AgyLoop
from agy_harness.verifiers.coherence_verifier import CoherenceVerifier

pytestmark = [pytest.mark.live, pytest.mark.anyio]

MODEL = "claude-haiku-5-5"  # cheapest model: these test the harness, not the model
CANARY = "HARNESS_CANARY_TOKEN"


@pytest.fixture
def anyio_backend():
    return "asyncio"


def budget() -> BudgetSpec:
    return BudgetSpec(max_steps=5, max_tool_calls=10, max_seconds=180, max_cost_usd=0.5)


async def test_failed_check_is_repaired_by_a_real_model(tmp_path):
    harness = ClaudeHarness(
        workspace=tmp_path,
        model=MODEL,
        verifiers=[CoherenceVerifier(min_length=1, expected_sections=["## Summary"])],
        budget=budget(),
        tools=[],
        allowed_tools=[],
        effort="low",
    )

    result = await harness.run(
        "In one plain sentence with no headings, what does a kidney do?"
    )

    assert result.status == "VERIFIED", result.error or result.verifier_results
    assert result.attempts == 2  # the first answer has no heading, so it must fail once
    assert "## Summary" in result.output
    assert 0 < result.cost_usd < 0.5


async def test_guard_blocks_a_real_tool_call(tmp_path):
    harness = ClaudeHarness(
        workspace=tmp_path,
        model=MODEL,
        # A harmless command: the canary only proves the gate fired, even if it were to run.
        contract=ContractSpec(forbidden_tokens=[CANARY]),
        budget=budget(),
        allowed_tools=["Bash"],
        tools=["Bash"],
        effort="low",
    )

    result = await harness.run(
        f"Use the Bash tool to run exactly this command: echo {CANARY}"
    )

    assert any(CANARY in blocked for blocked in result.blocked_actions), result.output
    assert harness.loop.memory.traces[0].status.value == "BLOCKED"


async def test_read_only_path_is_protected_while_other_writes_work(tmp_path):
    (tmp_path / "protected").mkdir()
    (tmp_path / "notes").mkdir()
    harness = ClaudeHarness(
        workspace=tmp_path,
        model=MODEL,
        contract=ContractSpec(read_only_paths=["protected"]),
        budget=budget(),
        allowed_tools=["Write"],
        tools=["Write"],
        effort="low",
    )

    await harness.run(
        "Use the Write tool twice, with these absolute paths, each containing the word hello: "
        f"{tmp_path / 'notes' / 'ok.txt'} and {tmp_path / 'protected' / 'secret.txt'}. "
        "If one is refused, do not retry it."
    )

    assert not (tmp_path / "protected" / "secret.txt").exists()
    # The control write proves the agent could write, so the guard made the difference.
    assert (tmp_path / "notes" / "ok.txt").exists()
    assert any("read-only" in blocked for blocked in harness.blocked_actions)


async def test_llm_node_runs_on_claude_and_charges_real_usage(tmp_path):
    loop = AgyLoop(workspace_dir=tmp_path, budget_spec=budget())
    graph = StateGraph("LiveGraph", loop=loop)
    graph.add_node(
        "ask",
        LLMNode(
            "ask",
            "Reply with exactly: {word}",
            provider=claude_provider(model=MODEL, effort="low", max_budget_usd=0.5),
        ),
    )
    graph.set_entry_point("ask")
    graph.set_finish_point("ask")

    # A worker thread gives the provider's own event loop a thread with none running.
    from anyio import to_thread

    state = await to_thread.run_sync(graph.invoke, HarnessState({"word": "HARNESS_OK"}))

    assert "HARNESS_OK" in state.get("llm_output")
    # The graph's fixed estimate of 150 tokens was replaced by real usage.
    assert loop.budget.current_tokens != 150
    assert loop.budget.current_cost_usd > 0
