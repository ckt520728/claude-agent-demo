"""Interactive multi-turn agent with ClaudeSDKClient and a custom in-process tool.

Usage:  uv run chat.py      (type 'exit' to quit)
"""

from datetime import datetime

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
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


async def main() -> None:
    options = ClaudeAgentOptions(
        model="claude-opus-5-5",
        mcp_servers={"utils": utils_server},
        # Custom MCP tools are named mcp__<server>__<tool>
        allowed_tools=["Read", "Glob", "Grep", "mcp__utils__current_time"],
        max_turns=20,
    )

    async with ClaudeSDKClient(options=options) as client:
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break
            if not user_input:
                continue

            await client.query(user_input)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")
                elif isinstance(message, ResultMessage) and message.is_error:
                    print(f"[error] {message.subtype}: {message.errors}")


if __name__ == "__main__":
    anyio.run(main)
