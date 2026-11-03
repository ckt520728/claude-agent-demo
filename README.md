# claude-agent-demo

Starter project for the Claude Agent SDK in Python (`claude-agent-sdk`), managed with [uv](https://docs.astral.sh/uv/) on Python 3.12.

## Run

```powershell
uv run main.py "Summarize the files in this folder"   # one-shot query()
uv run chat.py                                        # interactive ClaudeSDKClient + custom tool
```

## Test

```powershell
uv run pytest             # live tests are skipped
uv run pytest --run-live  # sends a real prompt to Claude (costs a little)
```

## Authentication

Copy `.env.example` to `.env` and put your key in it. The scripts and tests load it automatically, and `.env` is in `.gitignore`, so it is never committed.

```
ANTHROPIC_API_KEY=sk-ant-...
```

Without a `.env`, the SDK falls back to your Claude Code login. When `ANTHROPIC_API_KEY` is set, it takes priority and usage is billed to that API key.

## Files

- `main.py`: a one-shot `query()` call with read-only built-in tools (Read, Glob, Grep).
- `chat.py`: a multi-turn session using `ClaudeSDKClient`, with an in-process MCP tool (`current_time`).

Docs: https://code.claude.com/docs/en/agent-sdk
