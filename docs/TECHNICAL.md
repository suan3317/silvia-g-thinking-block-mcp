# Silvia & G Thinking Block MCP — Technical Notes

[Back to README](../README.md) · [简体中文](./TECHNICAL.zh-CN.md)

This document contains the mechanism, evidence, rendering boundary, context-retention limitation, and planned SDK architecture. The main README stays focused on setup, use, and customization.

## How it works

1. The host discovers `render_thinking_block` through `tools/list`.
2. The tool schema tells the model how to write the visible block and how `style` and `effort` behave.
3. The model calls the tool before its final answer.
4. The server returns a small text result plus the block data in tool-result metadata.
5. An MCP Apps HTML resource reads the tool input/result metadata and renders the card.
6. The model continues to the final answer with the tool call already present in the turn.

Our working hypothesis is that agentic models are trained around many repeated trajectories of **reason → call a tool → read the result → continue the answer**. A tool call can therefore act as a relatively stable learned trigger for planning and intermediate reasoning. When the tool schema explicitly asks the model to place that working state in a `thinking` argument, it is more likely to enter the planning-and-reasoning register associated with tool use. Compared with an ordinary prose request to “write out your reasoning,” the structured tool boundary can produce native-like reasoning output more consistently.

This is related to asking a model to “write out its reasoning,” but the tool-call boundary changes the interaction. In our experiments, tool-parameter induction consistently produced an intermediate register closer to the model's native reasoning style than an ordinary prose request. Because the tool call happens before the answer and remains part of the turn, it can also change the path of the eventual answer.

The implementation is deliberately small: one dependency-free Python server contains the MCP transport, REST/OpenAPI surface, tool schema, and HTML/CSS/JavaScript widget.

## `zh-CN` relational isolation boundary

This dedicated implementation defines `relational` as first-person, unspoken asides outside the final reply, not an emotional version of `deep_think`. Both use the same MCP tool and card, but the schema assigns separate roles: `deep_think` may handle tasks and evidence; `relational` may contain only present feelings, impulses, associations, hesitation, and thoughts omitted from the reply. It explicitly excludes task reasoning, response strategy, analytical frameworks, and user-needs analysis. Relational effort values impose no minimum length, and an empty string is allowed when there is no genuine movement.

These are generation constraints, not a server-side semantic validator. The server does not keyword-filter or rewrite submitted prose. Regression tests keep the important inclusions and exclusions present in the schema.

## What exactly is rendered?

The project does not decrypt a provider's encrypted reasoning payload. It renders a new, model-authored intermediate reasoning narrative produced for the tool call. That narrative is visible, editable, and steerable, and in our empirical comparison its form is closer to native reasoning output than ordinary “show your reasoning” prompting.

## Context retention in the MCP-only version

The model writes the block into `arguments.thinking`. Tool-result `_meta` is widget-only, but the original tool input remains part of the host's tool-call transcript. Copying the text into `_meta` does not erase that original input, so a later turn may still see and quote an earlier block. `CAPTURE_ENABLED=0` only guarantees that this server does not print or persist the content; it cannot delete a tool call stored by the host.

The included tool description labels earlier blocks as non-authoritative, current-turn scratch work and tells the model not to quote or carry them forward unless the user asks. This is a behavioral mitigation, not cryptographic isolation. Do not request secrets, credentials, or private internal data in a thinking block.

Standard MCP currently has no field that means “let the model generate and use this argument now, then remove it from the next turn.” This is the main context-isolation limit of the standalone MCP version.

## Codex SDK + custom frontend

We also have a separate architecture based on the [Codex SDK](https://developers.openai.com/codex/sdk) and a custom frontend. Because that application controls model settings and constructs the conversation context itself, it can:

- disable native reasoning with effort `none`, avoiding a separate hidden reasoning pass, its token cost, and the risk that it anchors the visible reasoning before the block is written;
- include the visible thinking block in the current turn so it can affect the final answer;
- omit that block and its tool-call arguments when constructing the next turn, while optionally retaining it only in the local UI or an audit record.

That gives the intended lifecycle: **generate → render → use for the current answer → discard from later model context**. It is an orchestration feature of the SDK/custom-frontend version, not a capability of this MCP server by itself. A separate implementation tutorial will be published later. [OpenAI's current model guidance](https://developers.openai.com/api/docs/guides/latest-model) documents both `reasoning.effort: "none"` and turn-scoped reasoning via `reasoning.context: "current_turn"`.

## Relevant implementation locations

- `TOOL` in [`server.py`](../server.py) defines the tool and input schema.
- `STYLE_DESCRIPTIONS` and `THINKING_DESCRIPTIONS` define the English and Chinese prompt editions.
- `WIDGET_HTML` contains the MCP Apps card.
- `handle()` implements the MCP methods and tool call.
- `openapi()` exposes the matching REST/OpenAPI schema.

