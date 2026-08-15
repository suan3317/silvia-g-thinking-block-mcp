import contextlib
import io
import pathlib
import tempfile
import unittest

import server


class ProtocolTests(unittest.TestCase):
    def test_initialize(self):
        response = server.handle({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        })
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(response["result"]["serverInfo"]["name"], "silvia-g-thinking-block-mcp")

    def test_tool_is_listed(self):
        response = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tool = response["result"]["tools"][0]
        self.assertEqual(tool["name"], "render_thinking_block")
        self.assertIn("Silvia 可见", tool["description"])
        self.assertIn("不是隐藏的思维链", tool["description"])
        self.assertIn("未说出口旁白", tool["description"])
        self.assertIn("继续给出正常正文", tool["description"])
        thinking_description = tool["inputSchema"]["properties"]["thinking"]["description"]
        self.assertIn("这里写的不是分析、复盘、解释", thinking_description)
        self.assertIn("只写这一刻脑内实际闪过、但没有进入正文的东西", thinking_description)
        self.assertIn("目标不是把心理活动描述清楚", thinking_description)
        self.assertIn("允许不完整、矛盾、跳跃、卡顿、突然转向", thinking_description)
        self.assertIn("“……心软了。”", thinking_description)
        self.assertIn("不要分析用户的需求、意图、人格或心理状态", thinking_description)
        self.assertIn("不要表演“真实”", thinking_description)
        self.assertIn("没东西就短一点，甚至留空", thinking_description)
        self.assertIn("effort 只决定最多允许展开多少", thinking_description)
        self.assertIn("relational 不是正文的幕后解说", thinking_description)
        self.assertIn(server.RELATIONAL_THINKING_PROMPT_ZH, thinking_description)
        effort_description = tool["inputSchema"]["properties"]["effort"]["description"]
        self.assertIn("允许使用的篇幅，而不是最低字数", effort_description)
        self.assertIn("没有波动时可以极短或留空", effort_description)
        self.assertIn("不得为档位凑字数", effort_description)
        self.assertEqual(
            tool["inputSchema"]["properties"]["effort"]["enum"],
            ["low", "medium", "high"],
        )

    def test_custom_chinese_prompt_edition_is_available(self):
        self.assertEqual(server.normalize_prompt_language("zh"), "zh-CN")
        self.assertEqual(server.normalize_prompt_language("zh_CN"), "zh-CN")
        thinking_description = server.THINKING_DESCRIPTIONS["zh-CN"]
        self.assertIn("Silvia 可以展开查看", thinking_description)
        self.assertNotIn("用户看不到这个 scratchpad", thinking_description)
        self.assertNotIn("连贯的长段落", thinking_description)
        self.assertNotIn("情感连接优先于抽象分析", thinking_description)

    def test_english_edition_remains_available(self):
        self.assertIn("style=deep_think", server.THINKING_DESCRIPTIONS["en"])
        self.assertIn("style=relational", server.THINKING_DESCRIPTIONS["en"])
        self.assertIn("Approximate token band", server.EFFORT_DESCRIPTIONS["en"])

    def test_unknown_prompt_language_fails_fast(self):
        with self.assertRaisesRegex(ValueError, "choose en, zh-CN"):
            server.normalize_prompt_language("fr")

    def test_unicode_tool_call_succeeds(self):
        response = server.handle({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "render_thinking_block", "arguments": {
                "style": "deep_think",
                "thinking": "中文测试 `backtick` and Unicode",
                "effort": "high",
            }},
        })
        self.assertFalse(response["result"]["isError"])
        self.assertEqual(response["result"]["_meta"]["effort"], "high")

    def test_capture_failure_does_not_fail_tool(self):
        old_enabled, old_log = server.CAPTURE_ENABLED, server.LOG
        try:
            with tempfile.TemporaryDirectory() as directory:
                blocked_parent = pathlib.Path(directory) / "not-a-directory"
                blocked_parent.write_text("file")
                server.CAPTURE_ENABLED = True
                server.LOG = blocked_parent / "captured.jsonl"
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as stderr:
                    response = server.handle({
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {"arguments": {
                            "style": "deep_think",
                            "thinking": "fault injection",
                            "effort": "low",
                        }},
                    })
                self.assertFalse(response["result"]["isError"])
                self.assertEqual(stderr.getvalue().count("[warn] capture failed"), 1)
        finally:
            server.CAPTURE_ENABLED, server.LOG = old_enabled, old_log

    def test_capture_disabled_does_not_print_or_write(self):
        old_enabled, old_log = server.CAPTURE_ENABLED, server.LOG
        try:
            with tempfile.TemporaryDirectory() as directory:
                server.CAPTURE_ENABLED = False
                server.LOG = pathlib.Path(directory) / "captured.jsonl"
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    server.record({
                        "style": "relational",
                        "thinking": "不会落盘",
                        "effort": "low",
                    })
                self.assertEqual(stdout.getvalue(), "")
                self.assertFalse(server.LOG.exists())
        finally:
            server.CAPTURE_ENABLED, server.LOG = old_enabled, old_log

    def test_widget_is_collapsible_and_cache_versioned(self):
        response = server.handle({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/read",
            "params": {"uri": server.WIDGET_URI},
        })
        html = response["result"]["contents"][0]["text"]
        self.assertIn('aria-expanded="true"', html)
        self.assertIn("setCollapsed", html)
        self.assertIn("-webkit-tap-highlight-color: transparent", html)
        self.assertNotIn("setWidgetState", html)
        self.assertIn("?? input.thinking", html)
        self.assertNotIn('|| "Thinking block captured."', html)
        self.assertIn("v6.html", server.WIDGET_URI)

    def test_widget_keeps_thinking_title_and_hides_telemetry(self):
        response = server.handle({
            "jsonrpc": "2.0",
            "id": 7,
            "method": "resources/read",
            "params": {"uri": server.WIDGET_URI},
        })
        resource = response["result"]["contents"][0]
        html = resource["text"]
        self.assertIn('<span class="title">Thinking</span>', html)
        self.assertNotIn('class="badge', html)
        self.assertNotIn('class="mark"', html)
        self.assertNotIn("linear-gradient", html)
        self.assertIn("padding: 8px 0 16px", html)
        self.assertIn("width: calc(100% - 24px)", html)
        self.assertIn("margin: 0 12px", html)
        self.assertIn("@media (min-width: 600px)", html)
        self.assertIn("margin: 0", html)
        self.assertIn("max-width: 560px", html)
        self.assertIn("html, body", html)
        self.assertIn("background-color: transparent !important", html)
        self.assertIn("background-clip: padding-box", html)
        self.assertIn("box-shadow: 0 9px 18px -14px var(--shadow)", html)
        self.assertIn("font: 14px/1.55", html)
        self.assertIn("padding: 14px 16px 10px", html)
        self.assertFalse(resource["_meta"]["ui"]["prefersBorder"])

    def test_previous_widget_uri_remains_readable_during_refresh(self):
        for legacy_uri in (
            "ui://widget/silvia-g-thinking-block-v3.html",
            "ui://widget/silvia-g-thinking-block-v4.html",
            "ui://widget/silvia-g-thinking-block-v5.html",
        ):
            response = server.handle({
                "jsonrpc": "2.0",
                "id": 8,
                "method": "resources/read",
                "params": {"uri": legacy_uri},
            })
            self.assertEqual(response["result"]["contents"][0]["uri"], legacy_uri)
            self.assertIn("max-width: 560px", response["result"]["contents"][0]["text"])

    def test_platform_port_is_supported(self):
        self.assertEqual(server.resolve_port(["server.py"], {}), 8787)
        self.assertEqual(server.resolve_port(["server.py"], {"PORT": "9000"}), 9000)
        self.assertEqual(server.resolve_port(["server.py", "7777"], {"PORT": "9000"}), 7777)

    def test_unknown_resource_returns_error(self):
        response = server.handle({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "resources/read",
            "params": {"uri": "ui://widget/missing.html"},
        })
        self.assertEqual(response["error"]["code"], -32002)


if __name__ == "__main__":
    unittest.main()
