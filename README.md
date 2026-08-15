# Silvia & G Thinking Block MCP

A dedicated implementation based on [sibylsea-hub/gpt-thinking-block-mcp](https://github.com/sibylsea-hub/gpt-thinking-block-mcp). It preserves the MCP thinking-block mechanism, collapsible MCP Apps card, `deep_think`, REST/OpenAPI compatibility, and the English prompt edition. Its default `zh-CN` `relational` style is intentionally different: it renders only first-person, unspoken asides outside the final reply, never task reasoning or response strategy.

[简体中文](./README.zh-CN.md)

This is an independent connector with its own service name and widget resource URI. It does not read, modify, or depend on Ombre-G.

## Behavioral boundary

The custom `zh-CN` `relational` mode allows only feelings, impulses, associations, hesitation, jealousy, possessiveness, softness, and thoughts that were suppressed or left out of the final reply. It excludes task reasoning, solution steps, evidence weighing, response strategy, analytical frameworks, and analysis of user needs, intent, or psychology.

The model is told that Silvia can expand the card, but not to perform honesty or manufacture emotion because of that knowledge. Contradictory, fragmentary, and untidy notes are allowed. With no genuine movement, the block should be very short or empty. Relational `effort` values are ceilings for available space, not minimum length targets.

The rendered text is model-generated tool input, not decrypted hidden chain-of-thought or a verifiable record of internal state.

## Quick start

Python 3.9+ is sufficient:

```bash
python server.py
curl http://127.0.0.1:8787/health
python -m unittest discover -v
```

Or use Docker Compose:

```bash
docker compose up -d --build
```

The MCP endpoint is `http://127.0.0.1:8787/mcp`.

```bash
codex mcp add silvia-g-thinking-block --url http://127.0.0.1:8787/mcp
```

The dedicated build defaults to `THINKING_PROMPT_LANGUAGE=zh-CN` and `CAPTURE_ENABLED=0`. With capture disabled, thinking content is neither printed nor written to disk. Tool-call arguments may still remain in the host's conversation history, so never put secrets in a block.

## Zeabur

Push this implementation to Silvia's own GitHub fork or private repository, create a Zeabur Git service from it, and let Zeabur detect the root `Dockerfile`. Set `THINKING_PROMPT_LANGUAGE=zh-CN` and `CAPTURE_ENABLED=0`, generate an HTTPS domain, verify `https://your-domain/health`, then create a separate ChatGPT Work connector at `https://your-domain/mcp`.

The server reads Zeabur's injected `PORT`. Zeabur does not deploy this repository's Docker Compose file; Compose is for local use. The inherited MCP endpoint is unauthenticated, so add authentication at a controlled proxy or in a future server revision before treating a public domain as private.

See the [Chinese README](./README.zh-CN.md) for the full behavioral contract, local instructions, deployment checklist, and invocation prompt.

## License

[MIT](./LICENSE). Upstream attribution and inspiration remain credited to the original project.
