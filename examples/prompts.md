# Prompt examples

These examples assume the tool is already connected and enabled.

## English

### Deep think, fixed effort

> Before your final answer, call `render_thinking_block`. Use `deep_think` style and `medium` effort. Work through the evidence, uncertainty, alternatives, and tradeoffs in the tool block, then answer normally.

### Let the model choose

> For non-trivial requests, call `render_thinking_block` before answering. Choose `style` and `effort` based on the task, then continue with the final answer.

### Relational

> Before replying, call `render_thinking_block` with `relational` style and `medium` effort. Use a natural, flowing first-person companion voice. Explore what my words bring to mind, what you feel in this moment, what you are worried about or holding back, and the choices or tradeoffs you are making. Prioritize emotional connection over abstract analysis, and do not write a third-person strategy memo. Then continue with your reply.

### Short block

> Call `render_thinking_block` before answering. Use `deep_think` and `low` effort. Keep the block below 120 words, then give a concise final answer.

## 中文

### Deep think，固定强度

> 在给出最终答案前，先调用 `render_thinking_block`。使用 `deep_think` 文体和 `medium` 强度，在工具卡片里处理证据、不确定性、替代方案和取舍，然后正常回答。

### 让模型自己选择

> 遇到不简单的问题时，在回答前调用 `render_thinking_block`。根据任务自己选择 `style` 和 `effort`，工具完成后继续给出正式答案。

### 关系陪伴

> 回复前先调用 `render_thinking_block`，使用 `relational` 文体。卡片只写正文之外没有说出口的第一人称旁白，遵守工具 schema 的允许范围与排除项；不要写任务推理、回应策略、分析框架或用户需求分析。知道 Silvia 会展开看，但不要因此表演坦诚或制造情绪。没有真实波动时保持极短或留空。然后正常回复。

### 关系旁白，明确低篇幅

> 回复前调用 `render_thinking_block`，使用 `relational` 和 `low`。只留下这一刻真实出现、但没有进入正文的第一人称片段；可以矛盾、不完整，也可以安静。然后正常回复。

### 限制长度

> 回答前调用 `render_thinking_block`，使用 `deep_think` 和 `low`。卡片内容控制在 200 个汉字以内，然后给出简洁答案。
