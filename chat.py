"""Interactive multi-turn agent with ClaudeSDKClient and a custom in-process tool.

Usage:  uv run chat.py      (type 'exit' to quit)
"""

import sys
from datetime import datetime

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ClaudeSDKError,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    tool,
)
from dotenv import load_dotenv

load_dotenv()  # picks up ANTHROPIC_API_KEY from .env if present


@tool("current_time", "Get the current local date and time", {})
async def current_time(args: dict) -> dict:
    return {
        "content": [
            {"type": "text", "text": datetime.now().isoformat(timespec="seconds")}
        ]
    }


utils_server = create_sdk_mcp_server(name="utils", tools=[current_time])


def report_failure(detail: str, last_text: str) -> None:
    # The CLI often echoes the error as assistant text; don't repeat it.
    suffix = "" if detail.strip() == last_text.strip() else f": {detail}"
    sys.stdout.flush()  # keep ordering with stderr when piped
    print(f"\n--- failed{suffix}", file=sys.stderr)


async def main() -> int:
    options = ClaudeAgentOptions(
        model="claude-opus-5-5",
        mcp_servers={"utils": utils_server},
        # Custom MCP tools are named mcp__<server>__<tool>
        allowed_tools=["Read", "Glob", "Grep", "mcp__utils__current_time"],
        max_turns=20,
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            while True:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    return 0
                if not user_input:
                    continue

                await client.query(user_input)
                failed = False
                last_text = ""
                try:
                    async for message in client.receive_response():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    print(f"Claude: {block.text}")
                                    last_text = block.text
                        elif isinstance(message, ResultMessage) and message.is_error:
                            failed = True
                            report_failure(
                                message.result
                                or "; ".join(message.errors or [])
                                or "unknown error",
                                last_text,
                            )
                except ClaudeSDKError as e:
                    # An error result alone keeps the session open (reported above);
                    # if the SDK raises, the connection is gone, so stop.
                    if not failed:
                        report_failure(str(e), last_text)
                    return 1
    except ClaudeSDKError as e:
        # Failed to start or lost the connection outside a turn.
        report_failure(str(e), "")
        return 1


if __name__ == "__main__":
    sys.exit(anyio.run(main))
