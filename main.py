"""One-shot agent run with query().

Usage:  uv run main.py "your prompt here"
"""

import sys

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)
from dotenv import load_dotenv

load_dotenv()  # picks up ANTHROPIC_API_KEY from .env if present


async def main(prompt: str) -> int:
    options = ClaudeAgentOptions(
        model="claude-opus-5-5",
        system_prompt="You are a concise, careful assistant working in this project folder.",
        allowed_tools=["Read", "Glob", "Grep"],  # read-only by default
        permission_mode="default",
        # Don't load your own Claude Code setup (settings, MCP servers,
        # plugins, skills): it can add ~200K tokens to every request.
        setting_sources=[],
        strict_mcp_config=True,
        skills=[],
        max_turns=10,
    )

    failed = False
    last_text = ""
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        last_text = block.text
                    elif isinstance(block, ToolUseBlock):
                        print(f"  [tool] {block.name} {block.input}")
            elif isinstance(message, ResultMessage):
                if message.is_error:
                    failed = True
                    detail = (
                        message.result
                        or "; ".join(message.errors or [])
                        or "unknown error"
                    )
                    # The CLI often echoes the error as assistant text; don't repeat it.
                    suffix = (
                        "" if detail.strip() == last_text.strip() else f": {detail}"
                    )
                    sys.stdout.flush()  # keep ordering with stderr when piped
                    print(f"\n--- failed{suffix}", file=sys.stderr)
                else:
                    cost = (
                        f"${message.total_cost_usd:.4f}"
                        if message.total_cost_usd
                        else "n/a"
                    )
                    print(
                        f"\n--- done: {message.subtype}, turns={message.num_turns}, cost={cost}"
                    )
    except ClaudeSDKError as e:
        # The SDK raises after an error result; only report it if not shown above.
        if not failed:
            sys.stdout.flush()
            print(f"\n--- failed: {e}", file=sys.stderr)
        return 1

    return 1 if failed else 0


if __name__ == "__main__":
    prompt = (
        " ".join(sys.argv[1:])
        or "List the files in this project and summarize what it is."
    )
    sys.exit(anyio.run(main, prompt))
