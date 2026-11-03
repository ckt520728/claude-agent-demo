# claude-agent-demo

Starter project for the Claude Agent SDK in Python (`claude-agent-sdk`), managed with [uv](https://docs.astral.sh/uv/) on Python 3.12.

## Run

```powershell
uv run main.py "Summarize the files in this folder"   # one-shot query()
uv run chat.py                                        # interactive ClaudeSDKClient + custom tool
```

Authentication is handled by the Claude Code CLI (an existing `claude` login), or by setting `ANTHROPIC_API_KEY`.

## Files

- `main.py`: a one-shot `query()` call with read-only built-in tools (Read, Glob, Grep).
- `chat.py`: a multi-turn session using `ClaudeSDKClient`, with an in-process MCP tool (`current_time`).

Docs: https://code.claude.com/docs/en/agent-sdk
