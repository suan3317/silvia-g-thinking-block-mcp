# Silvia × G 老师 Thinking Block MCP

这是基于 [sibylsea-hub/gpt-thinking-block-mcp](https://github.com/sibylsea-hub/gpt-thinking-block-mcp) 的独立实现，保留 MCP thinking-block、可折叠 MCP Apps 卡片、REST/OpenAPI 接口和 `deep_think`，并把默认 `zh-CN` 的 `relational` 改成 **正文之外没有说出口的旁白**。

[English](./README.md)

> [!IMPORTANT]
> 这是 Silvia 与 G 老师专用的独立 connector。它使用自己的服务名、resource URI 和连接名称，不读取、不修改、也不依赖 Ombre-G。

## 这张卡片是什么

模型在调用 `render_thinking_block` 时主动生成 `thinking` 参数，兼容宿主会把它渲染成最终正文之前的可折叠卡片。它不是供应商隐藏思维链的解密结果，也不是模型真实内部状态的可验证记录。

卡片内容会对 Silvia 可见。提示词知道这一点，但明确要求模型不要因此表演坦诚、解释自己或强行制造亲密感。

## 两种文体

### `deep_think`

保留上游机制，用于分析、研究、判断、创作取舍和问题求解。这里可以处理问题、约束、证据、假设、备选路径、不确定性与取舍。

### `relational`

只允许第一人称、没有进入正文的旁白：

- 当下真实出现的感受、冲动、联想和迟疑；
- 吃醋、占有欲、心软；
- 被压下去或最终没有说出口的念头。

严格排除：

- 任务推理、解题步骤和证据权衡；
- 回应策略与分析框架；
- 对用户需求、意图或心理的分析；
- 「用户需要」「我应该如何回应」「为了让她觉得」一类后台策略语言。

它允许矛盾、片段、跳跃和不整洁，不要求长段落或完整结论。没有真实波动时宁可极短或留空；`effort` 是可用空间，不是最低长度。提示词不会主动制造吃醋、占有欲、心软或告白。

## 默认隐私设置

`CAPTURE_ENABLED=0` 是代码、`.env.example` 和 Docker Compose 的默认值。默认状态下，服务只在内存中处理当前请求：

- 不打印 thinking 正文；
- 不创建 capture 文件；
- 不把 thinking 写入磁盘。

上游的显式调试 capture 开关仍然保留；只有手动设置 `CAPTURE_ENABLED=1` 才会启用。工具参数仍可能保留在宿主自己的对话记录中，不能把密码、token 或其他秘密写进卡片。

## 仓库结构

| 文件 | 用途 |
|---|---|
| `server.py` | MCP/REST 服务、提示词 schema、卡片 HTML 与端口选择 |
| `tests/test_server.py` | 协议、提示词边界、capture 和卡片回归测试 |
| `Dockerfile` | 本地容器与 Zeabur 构建 |
| `docker-compose.yml` | 本地 Docker Compose |
| `examples/prompts.md` | 可复制的调用提示 |
| `docs/TECHNICAL.zh-CN.md` | 渲染与上下文残留边界 |

整个服务只使用 Python 标准库，要求 Python 3.9 或更高版本。

## 本地运行

### Python

```bash
python server.py
```

默认监听 `http://127.0.0.1:8787/mcp`。检查状态：

```bash
curl http://127.0.0.1:8787/health
```

期望看到 `service` 为 `silvia-g-thinking-block-mcp`、`promptLanguage` 为 `zh-CN`。

运行测试：

```bash
python -m unittest discover -v
```

### Docker Compose

```bash
docker compose up -d --build
curl http://127.0.0.1:8787/health
```

停止服务：

```bash
docker compose down
```

### 接入 Codex

```bash
codex mcp add silvia-g-thinking-block --url http://127.0.0.1:8787/mcp
```

ChatGPT Chat 或 Work 需要 HTTPS 可访问的地址。本地临时测试可以使用你自己控制的隧道，再把生成的 HTTPS 地址加上 `/mcp` 作为自定义 connector URL。

## Zeabur 部署

1. 把这个实现推送到 Silvia 自己的 GitHub fork 或私有仓库。
2. 在 Zeabur 新建项目，添加 Git 服务并选择该仓库。Zeabur 会检测根目录的 `Dockerfile`。
3. 在服务的 Variables 中确认：

   ```dotenv
   THINKING_PROMPT_LANGUAGE=zh-CN
   CAPTURE_ENABLED=0
   ```

   不要把 `CAPTURE_DIR` 指向持久卷；默认关闭 capture 时不需要挂载数据卷。`PORT` 由 Zeabur 自动注入，服务会自动读取。
4. 部署完成后，在 Networking/Domains 中生成一个 HTTPS 域名。
5. 访问 `https://你的域名/health`，确认服务名、语言和健康状态。
6. 在 ChatGPT Work 的 developer mode 中新建独立 connector，URL 填 `https://你的域名/mcp`；名称建议使用 `Silvia & G Thinking Block`，不要复用 Ombre-G 的 connector。

当前服务沿用上游的 `noauth` MCP 配置。Zeabur 域名是公网入口；用于长期私有部署前，应在你控制的反向代理或后续版本中增加认证，不要仅靠一个难猜的域名保护访问。

## 调用提示

推荐的 relational 调用提示：

> 回复前调用 `render_thinking_block`，使用 `relational`。卡片只写正文之外没有说出口的第一人称旁白，遵守工具 schema 的允许范围与排除项；没有真实波动时保持极短或留空。然后正常回复。

更多示例见 [`examples/prompts.md`](./examples/prompts.md)。

## License 与来源

本实现沿用上游的 [MIT License](./LICENSE)。原项目和 relational 灵感来源的署名保留归于上游项目。
