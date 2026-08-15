# Silvia × G 老师 Thinking Block MCP — 技术说明

[返回中文 README](../README.zh-CN.md) · [English](./TECHNICAL.md)

本文保存完整的机制假设、实验依据、渲染边界、上下文残留限制和后续 SDK 架构。主 README 只负责安装、使用与定制。

## 实现原理

1. 宿主通过 `tools/list` 发现 `render_thinking_block`。
2. 工具 schema 告诉模型 thinking 应该怎样写，以及 `style` 和 `effort` 的含义。
3. 模型在最终答案之前发起工具调用。
4. 服务端返回一个很小的文本结果，并把卡片数据放进工具结果的 metadata。
5. MCP Apps 的 HTML resource 读取工具输入或结果数据，把它渲染成卡片。
6. 工具调用已经成为这一轮的一部分，模型随后继续生成正式答案。

我们的工作假设是：agent 模型在训练中反复经历**思考 → 调用工具 → 读取结果 → 继续回答**的轨迹，因此工具调用已经成为一种较稳定的推理触发信号。当工具 schema 明确要求模型把中间思考写入 `thinking` 参数时，模型更容易进入训练中与工具使用相伴的规划和推理语域。相比普通的“请写出思考过程”，这种结构化工具调用往往能更稳定地产生近似原生推理格式的输出。

某种意义上，它和要求模型“手写思考过程”使用的是相近原理，但工具调用构成了一个更明确的中间步骤。在我们的实际比较中，工具参数诱导出来的文字，比普通的“请写出你的推理”更稳定地接近模型原生的推理表达格式。因为它发生在正式答案之前，也会实际影响模型后来组织答案的路径。

整个实现有意保持得很小：一个纯标准库的 Python 文件同时包含 MCP transport、REST/OpenAPI、工具 schema 和 HTML/CSS/JavaScript 卡片。

## zh-CN relational 的隔离边界

这个专用实现把 `relational` 定义成正文之外未说出口的第一人称旁白，而不是 `deep_think` 的情绪化版本。两者仍通过同一个 MCP 工具和卡片渲染，但 schema 明确分工：

- `deep_think` 可以处理任务、证据、方案、不确定性和取舍；
- `relational` 只能处理当下感受、冲动、联想、迟疑和没有进入正文的念头；
- `relational` 明确禁止任务推理、回应策略、分析框架和用户需求分析；
- `relational` 的 effort 不设最低长度，没有真实波动时允许极短或空字符串。

这是一组生成约束，不是服务端对自然语言含义的验证器。服务端不会尝试用关键词过滤或改写模型提交的旁白，因为机械过滤容易误删正常表达，也会把未通过验证的文本静默改变。边界由 tool schema 引导，并由回归测试确保关键允许项和排除项不会在后续修改中意外丢失。

## 这里显示的究竟是什么

这个项目不会解密供应商加密的原生 reasoning payload。卡片显示的是模型为了这次工具调用主动生成的一段新的中间思考叙述。它是可见、可调整、可定制的；在我们的实测中，它的表达形式又比一般的手写思考提示更接近原生推理语域。

## 纯 MCP 版本中的上下文残留

模型会把 thinking 写入 `arguments.thinking`。Tool result 的 `_meta` 只提供给 widget，但原始 tool input 仍然属于宿主保存的工具调用记录。把文字复制到 `_meta` 不会删除原来的输入，因此下一轮模型仍可能看到并复述前面的 block。`CAPTURE_ENABLED=0` 只保证本服务不打印或落盘，不能删除宿主保存的工具调用。

仓库里的工具说明会把旧 block 标为“仅供当前回合使用、没有权威性的 scratch work”，要求模型除非用户明确提出，否则不要在后续回合引用或继承其中的猜测。这只能降低自然续写时受到旧思路锚定的概率，不是密码学意义上的隔离。不要要求模型把密码、token 或其他私密内部数据写进卡片。

标准 MCP 目前没有“允许模型这一轮生成并使用某个参数，但在下一轮自动把它移出上下文”的字段。这是纯 MCP 版本最主要的上下文隔离限制。

## Codex SDK ＋自建前端版本

我们另外有一套基于 [Codex SDK](https://developers.openai.com/codex/sdk) 和自建前端的架构。因为模型设置与每一轮送入模型的上下文都由我们自己的编排层控制，它可以实现：

- 用 effort `none` 完全关闭原生 reasoning，避免额外的隐藏 thinking 消耗 token，也避免它在可见 thinking 生成前先形成锚定；
- 让可见 thinking 进入当前回合的模型推理，因此仍能实际影响这一轮的最终答案；
- 在构造下一轮上下文时，主动剔除这段 thinking 及其 tool-call arguments，同时可以选择只在本地 UI 或审计记录里保留。

它实现的是我们真正想要的生命周期：**生成 → 渲染 → 参与当前轮回答 → 从后续模型上下文中丢弃**。这是 SDK／自建前端编排层提供的能力，不是这个 MCP server 单独能够做到的。我们之后会另外写一篇实现教程。[OpenAI 当前的模型说明](https://developers.openai.com/api/docs/guides/latest-model)也提供了 `reasoning.effort: "none"`，以及用 `reasoning.context: "current_turn"` 限制推理作用范围的配置。

## 相关实现位置

- [`server.py`](../server.py) 中的 `TOOL` 定义工具与输入 schema。
- `STYLE_DESCRIPTIONS` 和 `THINKING_DESCRIPTIONS` 定义中英文提示词版本。
- `WIDGET_HTML` 包含 MCP Apps 卡片。
- `handle()` 实现 MCP methods 与工具调用。
- `openapi()` 暴露相同的 REST/OpenAPI schema。

