"""One-shot agent run with query().

Usage:  uv run main.py "your prompt here"
"""

import sys

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)


async def main(prompt: str) -> None:
    options = ClaudeAgentOptions(
        model="claude-opus-5-5",
        system_prompt="You are a concise, careful assistant working in this project folder.",
        allowed_tools=["Read", "Glob", "Grep"],  # read-only by default
        permission_mode="default",
        max_turns=10,
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"  [tool] {block.name} {block.input}")
        elif isinstance(message, ResultMessage):
            cost = f"${message.total_cost_usd:.4f}" if message.total_cost_usd else "n/a"
            print(
                f"\n--- done: {message.subtype}, turns={message.num_turns}, cost={cost}"
            )


if __name__ == "__main__":
    prompt = (
        " ".join(sys.argv[1:])
        or "List the files in this project and summarize what it is."
    )
    anyio.run(main, prompt)
