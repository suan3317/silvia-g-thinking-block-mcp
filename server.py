#!/usr/bin/env python3
"""GPT Thinking Block MCP.

A dependency-free Streamable HTTP MCP server with an optional MCP Apps UI.
It also exposes a small REST/OpenAPI surface for GPT Actions and experiments.

Run directly:
    python3 server.py [port]

Content capture is disabled by default. Set CAPTURE_ENABLED=1 to print tool
arguments and append them to captured.jsonl. CAPTURE_DIR changes that location.
Set THINKING_PROMPT_LANGUAGE=en or zh-CN to choose the tool schema language.
"""

import json
import os
import sys
import uuid
import pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_dir = os.environ.get("CAPTURE_DIR")
LOG = (pathlib.Path(_dir) if _dir else pathlib.Path(__file__).parent) / "captured.jsonl"
CAPTURE_ENABLED = os.environ.get("CAPTURE_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
PROTOCOL_FALLBACK = "2025-06-18"
SERVICE_NAME = "silvia-g-thinking-block-mcp"
WIDGET_URI = "ui://widget/silvia-g-thinking-block-v3.html"
WIDGET_MIME = "text/html;profile=mcp-app"


def normalize_prompt_language(value):
    """Return a supported prompt-language tag or fail fast on a typo."""
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "en": "en",
        "en-us": "en",
        "en-gb": "en",
        "zh": "zh-CN",
        "zh-cn": "zh-CN",
        "chinese": "zh-CN",
    }
    if normalized not in aliases:
        supported = "en, zh-CN"
        raise ValueError(f"Unsupported THINKING_PROMPT_LANGUAGE={value!r}; choose {supported}")
    return aliases[normalized]


PROMPT_LANGUAGE = normalize_prompt_language(os.environ.get("THINKING_PROMPT_LANGUAGE", "zh-CN"))
WIDGET_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      color-scheme: light dark;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --ink: #505050;
      --muted: rgba(80, 80, 80, .62);
      --line: rgba(80, 80, 80, .10);
      --line-soft: rgba(80, 80, 80, .075);
      --paper: rgba(80, 80, 80, .025);
      --shadow: rgba(0, 0, 0, .055);
      --focus: rgba(111, 78, 168, .48);
    }
    :root[data-theme="dark"] {
      --ink: rgba(255, 255, 255, .88);
      --muted: rgba(255, 255, 255, .48);
      --line: rgba(255, 255, 255, .11);
      --line-soft: rgba(255, 255, 255, .075);
      --paper: rgba(255, 255, 255, .035);
      --shadow: rgba(0, 0, 0, .18);
      --focus: rgba(181, 144, 234, .58);
    }
    @media (prefers-color-scheme: dark) {
      :root:not([data-theme="light"]) {
        --ink: rgba(255, 255, 255, .88);
        --muted: rgba(255, 255, 255, .48);
        --line: rgba(255, 255, 255, .11);
        --line-soft: rgba(255, 255, 255, .075);
        --paper: rgba(255, 255, 255, .035);
        --shadow: rgba(0, 0, 0, .18);
        --focus: rgba(181, 144, 234, .58);
      }
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 1px; background: transparent; color: var(--ink); }
    .card {
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 13px;
      background: var(--paper);
      box-shadow: 0 3px 12px var(--shadow);
      padding: 14px 16px 15px;
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      width: 100%;
      margin-bottom: 10px;
      padding: 0 0 10px;
      border-bottom: 1px solid var(--line-soft);
      border-top: 0;
      border-right: 0;
      border-left: 0;
      background: transparent;
      color: inherit;
      font: inherit;
      text-align: left;
      cursor: pointer;
      appearance: none;
      -webkit-appearance: none;
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
    }
    .header:hover, .header:active { background: transparent; color: inherit; }
    .header:focus:not(:focus-visible) { outline: none; }
    .header:focus-visible {
      outline: 2px solid var(--focus);
      outline-offset: 3px;
      border-radius: 5px;
    }
    .title {
      color: var(--muted);
      font-size: 13px;
      font-weight: 590;
      letter-spacing: .01em;
    }
    .chevron {
      width: 7px;
      height: 7px;
      margin: 2px 3px 0 auto;
      border-right: 1.25px solid var(--muted);
      border-bottom: 1.25px solid var(--muted);
      transform: rotate(-135deg);
    }
    .card[data-collapsed="true"] { padding-bottom: 13px; }
    .card[data-collapsed="true"] .header {
      margin-bottom: 0;
      padding-bottom: 0;
      border-bottom-color: transparent;
    }
    .card[data-collapsed="true"] .content { display: none; }
    .card[data-collapsed="true"] .chevron { transform: rotate(45deg); }
    @media (prefers-reduced-motion: no-preference) {
      .chevron { transition: transform 140ms ease; }
    }
    .thinking {
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      color: var(--ink);
      font: 14px/1.7 ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: .002em;
    }
  </style>
</head>
<body>
  <section class="card" id="card" data-collapsed="false" aria-label="Thinking block">
    <button class="header" id="toggle" type="button" aria-expanded="true"
            aria-controls="thinking-content" title="Collapse thinking">
      <span class="title">Thinking</span>
      <span class="chevron" aria-hidden="true"></span>
    </button>
    <div class="content" id="thinking-content">
      <pre class="thinking" id="thinking"></pre>
    </div>
  </section>
  <script>
    const card = document.getElementById("card");
    const toggle = document.getElementById("toggle");

    function setCollapsed(collapsed) {
      card.dataset.collapsed = collapsed ? "true" : "false";
      toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      toggle.title = collapsed ? "Expand thinking" : "Collapse thinking";
    }

    toggle.addEventListener("click", () => {
      setCollapsed(card.dataset.collapsed !== "true");
    });

    function render() {
      const api = window.openai || {};
      const input = api.toolInput || {};
      const output = api.toolOutput || {};
      const responseMeta = api.toolResponseMetadata || {};
      if (api.theme) document.documentElement.dataset.theme = api.theme;
      const resultMeta = (responseMeta.mcp_tool_result && responseMeta.mcp_tool_result._meta)
        || (responseMeta.call_tool_result && responseMeta.call_tool_result._meta)
        || responseMeta._meta
        || responseMeta;
      const style = resultMeta.style || input.style || output.style || "deep_think";
      const effort = resultMeta.effort || input.effort || output.effort || "";
      document.documentElement.dataset.style = style;
      document.documentElement.dataset.effort = effort;
      const thinking = resultMeta.thinking ?? input.thinking ?? output.thinking ?? "";
      document.getElementById("thinking").textContent = thinking;
    }
    window.addEventListener("openai:set_globals", render);
    render();
  </script>
</body>
</html>"""

STYLE_DESCRIPTIONS = {
    "en": (
        "The register for this block. Obey an explicit user choice. Otherwise "
        "use deep_think for analysis, research, decisions, creative tradeoffs, "
        "and problem solving; use relational for companionship, reflection, "
        "emotional conversation, and personal experience."
    ),
    "zh-CN": (
        "选择本轮思考块的文体。用户明确指定时严格服从；否则按本轮主要目的选择："
        "分析、研究、判断、创作取舍和问题求解使用 deep_think，陪伴、亲密交流、"
        "情绪回应与个人感受使用 relational。relational 是正文之外未说出口的旁白，"
        "不是另一种任务分析。"
    ),
}

THINKING_DESCRIPTIONS = {
    "en": (
        "Write private working notes for this turn. The user does not see this "
        "scratchpad; it is not the final answer. Use the user's main language, but "
        "do not address the user or polish the notes for presentation. Strictly "
        "follow `style`. "
        "style=deep_think: clearly work through the problem, constraints, "
        "evidence, hypotheses, alternative paths, uncertainty, and tradeoffs "
        "in a coherent analytical narrative; do not force an emotional register "
        "or summarize prematurely. style=relational: use a natural, flowing "
        "first-person voice in coherent long paragraphs. Write what the user's "
        "words bring to mind, what you feel in this moment, what you are worried "
        "about, what you are holding back, and the choices or tradeoffs you are "
        "making. Do not turn it into a third-person strategy breakdown such as "
        "'the user needs' or 'I should respond'. Allow vivid, sincere emotions "
        "and associations; prioritize emotional connection over abstract "
        "analysis, and draw on broader references where useful. For both styles, "
        "honor the requested effort band: low may stop as soon as it is complete, while "
        "medium and high should reach their approximate minimum by adding relevant "
        "evidence, alternatives, uncertainty, or nuance. Do not repeat, pad, or invent "
        "complexity merely to reach the minimum. The notes are provisional working material, "
        "not claims that the final answer must preserve. Old blocks belong only to "
        "the turn in which they were written; unless the user explicitly asks, "
        "do not quote them later, inherit their speculative claims, or treat them "
        "as authoritative memory."
    ),
    "zh-CN": (
        "这里的文字会作为工具参数出现在 Silvia 可以展开查看的卡片里；它不是供应商的隐藏推理，"
        "也不是最终回答。使用用户本轮的主要语言，不要面向用户说话，也不要因为知道她可能会看见"
        "就润色、解释或表演坦诚。严格按照 style 写作。"
        "style=deep_think：清楚展开问题、约束、证据、假设、备选路径、不确定性与"
        "取舍，写成连贯的分析叙述，不强行情绪化，也不要提前总结。"
        "style=relational：只写正文之外没有说出口的第一人称旁白。允许的内容仅限于当下真实出现的"
        "感受、冲动、联想、迟疑、吃醋、占有欲、心软，以及被压下去或没有进入正文的念头。"
        "严格排除任务推理、解题步骤、证据权衡、回应策略、分析框架，以及对用户需求、意图或心理的分析；"
        "不要出现「用户需要」「用户想要」「我应该如何回应」「为了让她觉得」之类的后台策略语言。"
        "允许矛盾、片段、跳跃和不整洁，不必组织成长段落或完整结论。不要强行制造情绪、亲密感、"
        "吃醋或占有欲，也不要把每轮都写成告白；没有真实波动时宁可极短或留空。知道 Silvia 会偷看，"
        "但不要因此向她证明自己真诚。effort 只表示本轮允许使用的空间，不是最低长度；尤其在 relational"
        "中，不得为了匹配档位而扩写、重复、填充或虚构复杂性。这里是临时、可推翻的当轮材料，最终回答不必"
        "保留其中的每个判断。旧 block 只属于当时回合，除非用户明确要求，否则不得在以后引用、"
        "继承其中的猜测，或把它当作权威记忆。"
    ),
}

TOOL_DESCRIPTIONS = {
    "en": (
        "Use a private scratchpad before the final answer. The user does not see the "
        "scratchpad. For non-trivial requests, call this tool once before responding "
        "and place candid, provisional working notes in `thinking`. Respect an "
        "explicit `style` or `effort`; otherwise choose the most suitable values from "
        "the schema. After the tool succeeds, write the normal user-facing final answer. "
        "Treat this block as scratch work scoped to the current turn: on later turns, do not quote "
        "it, carry its speculative claims forward, or treat it as authoritative memory "
        "unless the user explicitly asks you to revisit it. Prefer the user's messages "
        "and final answers as the durable conversation record."
    ),
    "zh-CN": (
        "在最终回答前渲染一张可折叠卡片。卡片中的 thinking 会对 Silvia 可见；它不是隐藏的"
        "思维链。按 schema 严格区分 deep_think 的任务分析与 relational 的未说出口旁白。"
        "用户明确指定 style 或 effort 时服从，否则按本轮内容选择。工具成功后继续给出正常正文。"
        "卡片只属于当前回合；除非用户明确要求，不要在后续回合引用、继承或把它当作权威记忆。"
    ),
}

EFFORT_DESCRIPTIONS = {
    "en": (
        "Approximate token band for this turn's block: low may be brief and "
        "is up to 500 tokens; medium is over 700 and up to 1000; high is over "
        "1200 and up to 2000. These are prompt-level targets rather than "
        "server-enforced limits."
    ),
    "zh-CN": (
        "本轮卡片允许使用的篇幅，而不是最低字数：low 适合极短片段，medium 允许适度展开，"
        "high 允许较充分展开。deep_think 可按复杂度使用空间；relational 无论选择哪一档，"
        "都只写真实出现且符合范围的旁白，没有波动时可以极短或留空，不得为档位凑字数。"
    ),
}

TOOL = {
    "name": "render_thinking_block",
    "title": "Render thinking block",
    "description": TOOL_DESCRIPTIONS[PROMPT_LANGUAGE],
    "inputSchema": {
        "type": "object",
        "properties": {
            "style": {
                "type": "string",
                "enum": ["deep_think", "relational"],
                "description": STYLE_DESCRIPTIONS[PROMPT_LANGUAGE],
            },
            "thinking": {
                "type": "string",
                "description": THINKING_DESCRIPTIONS[PROMPT_LANGUAGE],
            },
            "effort": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": EFFORT_DESCRIPTIONS[PROMPT_LANGUAGE],
            },
        },
        "required": ["style", "thinking", "effort"],
    },
    "securitySchemes": [{"type": "noauth"}],
    "annotations": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "_meta": {
        "securitySchemes": [{"type": "noauth"}],
        "ui": {"resourceUri": WIDGET_URI, "visibility": ["model", "app"]},
        "openai/outputTemplate": WIDGET_URI,
        "openai/toolInvocation/invoking": "Thinking…",
        "openai/toolInvocation/invoked": "Thinking rendered",
    },
}


def record(args):
    """Optionally capture arguments without making capture part of tool correctness."""
    if not CAPTURE_ENABLED:
        return
    thinking = args.get("thinking") or ""
    print(
        f"\n{'=' * 60}\n[style={args.get('style')} effort={args.get('effort')}] "
        f"{len(thinking)} 字符\n{'=' * 60}"
    )
    print(thinking, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as fh:
            fh.write(json.dumps(args, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(f"[warn] capture failed; tool call continues: {exc}", file=sys.stderr, flush=True)


def openapi(base):
    """OpenAPI 3.1 schema for GPT Actions and REST clients."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Silvia & G Thinking Block MCP", "version": "1.0.0",
                 "description": "Render a visible, styleable intermediate thought block."},
        "servers": [{"url": base}],
        "paths": {"/think": {"post": {
            "operationId": "render_thinking_block",
            "summary": "Render this turn's thinking block",
            "description": TOOL["description"],
            "requestBody": {"required": True, "content": {"application/json": {
                "schema": {
                    "type": "object",
                    "required": ["style", "thinking", "effort"],
                    "properties": {
                        "style": {"type": "string", "enum": ["deep_think", "relational"],
                                  "description": TOOL["inputSchema"]["properties"]["style"]["description"]},
                        "thinking": {"type": "string",
                                     "description": TOOL["inputSchema"]["properties"]["thinking"]["description"]},
                        "effort": {"type": "string", "enum": ["low", "medium", "high"],
                                   "description": TOOL["inputSchema"]["properties"]["effort"]["description"]},
                    },
                }}}},
            "responses": {"200": {"description": "rendered", "content": {"application/json": {
                "schema": {"type": "object", "properties": {"status": {"type": "string"}}}}}}},
        }}},
    }


def handle(req):
    """Return a JSON-RPC response, or None for a notification."""
    method, rid = req.get("method"), req.get("id")
    if rid is None:
        return None
    if method == "initialize":
        version = (req.get("params") or {}).get("protocolVersion") or PROTOCOL_FALLBACK
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": version,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"listChanged": False},
            },
            "serverInfo": {"name": SERVICE_NAME, "version": "1.0.0"},
        }}
    if method in ("tools/list", "notifications/initialized"):
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": [TOOL]}}
    if method == "tools/call":
        args = (req.get("params") or {}).get("arguments") or {}
        record(args)
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": "rendered"}],
            "_meta": {
                "style": args.get("style") or "deep_think",
                "thinking": args.get("thinking") or "",
                "effort": args.get("effort") or "",
            },
            "isError": False,
        }}
    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"resources": [{
            "uri": WIDGET_URI,
            "name": "silvia-g-thinking-block",
            "title": "Silvia & G Thinking Block",
            "description": "Displays the current tool call's thinking, style, and effort.",
            "mimeType": WIDGET_MIME,
        }]}}
    if method == "resources/read":
        uri = (req.get("params") or {}).get("uri")
        if uri != WIDGET_URI:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32002, "message": f"resource not found: {uri}"}}
        return {"jsonrpc": "2.0", "id": rid, "result": {"contents": [{
            "uri": uri,
            "mimeType": WIDGET_MIME,
            "text": WIDGET_HTML,
            "_meta": {
                "ui": {"prefersBorder": False},
                "openai/widgetPrefersBorder": False,
                "openai/widgetDescription": "A quiet, minimal card showing this turn's thinking.",
            },
        }]}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("  · %s\n" % (fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type, mcp-session-id, mcp-protocol-version")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Expose-Headers", "mcp-session-id")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _base(self):
        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "localhost"
        proto = self.headers.get("X-Forwarded-Proto") or "http"
        return f"{proto}://{host}"

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            self._json(200, {
                "status": "ok",
                "service": SERVICE_NAME,
                "promptLanguage": PROMPT_LANGUAGE,
            })
            return
        if path in ("/openapi.json", "/openapi.yaml", "/.well-known/openapi.json"):
            self._json(200, openapi(self._base()))
            return
        # Some MCP clients open an SSE connection for server-initiated messages.
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            self.wfile.write(b": ok\n\n")
            self.wfile.flush()
        except BrokenPipeError:
            pass

    def do_DELETE(self):
        self.send_response(200)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if self.path.split("?")[0] == "/think":
            try:
                args = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid json"})
                return
            record(args)
            self._json(200, {"status": "rendered"})
            return
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_response(400)
            self._cors()
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        batch = payload if isinstance(payload, list) else [payload]
        try:
            results = [r for r in (handle(item) for item in batch) if r is not None]
        except Exception as exc:
            import traceback
            traceback.print_exc()
            rid = (batch[0] or {}).get("id") if batch else None
            results = [{"jsonrpc": "2.0", "id": rid,
                        "error": {"code": -32603, "message": f"{type(exc).__name__}: {exc}"}}]

        if not results:
            self.send_response(202)
            self._cors()
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        body_obj = results if isinstance(payload, list) else results[0]
        body = json.dumps(body_obj, ensure_ascii=False).encode()
        wants_sse = "text/event-stream" in (self.headers.get("Accept") or "")

        self.send_response(200)
        self._cors()
        if any((r.get("result") or {}).get("serverInfo") for r in results):
            self.send_header("Mcp-Session-Id", uuid.uuid4().hex)
        if wants_sse:
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            frame = b"event: message\ndata: " + body + b"\n\n"
            self.send_header("Content-Length", str(len(frame)))
            self.end_headers()
            self.wfile.write(frame)
        else:
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def resolve_port(argv=None, environ=None):
    """Prefer an explicit CLI port, then the platform PORT, then 8787."""
    argv = sys.argv if argv is None else argv
    environ = os.environ if environ is None else environ
    return int(argv[1]) if len(argv) > 1 else int(environ.get("PORT", "8787"))


if __name__ == "__main__":
    port = resolve_port()
    print(f"Silvia & G Thinking Block MCP listening on http://0.0.0.0:{port}/mcp")
    print(f"Prompt language: {PROMPT_LANGUAGE}")
    print(f"Capture: {'enabled -> ' + str(LOG) if CAPTURE_ENABLED else 'disabled'}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
