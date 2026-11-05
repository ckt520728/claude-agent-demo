"""Agent run under the agy-harness control plane.

Tool calls pass a safety gate and a budget, the answer is checked by verifiers,
and failed checks are sent back to Claude for repair.

Usage:  uv run harness_agent.py "your prompt here"
"""

import sys

import anyio
from agy_harness.core.types import BudgetSpec
from agy_harness.integrations.claude_sdk import ClaudeHarness
from agy_harness.verifiers.coherence_verifier import CoherenceVerifier
from dotenv import load_dotenv

load_dotenv()  # picks up ANTHROPIC_API_KEY from .env if present


async def main(prompt: str) -> int:
    harness = ClaudeHarness(
        workspace=".",
        role="You are a concise, careful assistant working in this project folder.",
        constraints=["Only state what you verified from the files you read."],
        verifiers=[CoherenceVerifier(min_length=20)],
        budget=BudgetSpec(
            max_steps=5, max_tool_calls=20, max_seconds=300, max_cost_usd=1.0
        ),
        allowed_tools=["Read", "Glob", "Grep"],  # read-only by default
        max_repairs=1,
    )

    result = await harness.run(prompt)

    print(result.output)
    for blocked in result.blocked_actions:
        print(f"  [blocked] {blocked}")
    for check in result.verifier_results:
        print(f"  [check] {check.verifier_name}: passed={check.passed} {check.message}")
    print(
        f"\n--- {result.status}: attempts={result.attempts}, "
        f"tokens={result.tokens}, cost=${result.cost_usd:.4f}"
    )
    if result.error:
        print(f"--- error: {result.error}", file=sys.stderr)
    return 0 if result.passed else 1


if __name__ == "__main__":
    prompt = (
        " ".join(sys.argv[1:])
        or "List the files in this project and summarize what it is."
    )
    sys.exit(anyio.run(main, prompt))
