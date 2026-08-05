# DeepSeek Harness 内测报名文案

仓库：https://github.com/sutongwuyanzu/TaskHandoff  
版本：**v0.2.6** @ `479f3bd`  
CI：https://github.com/sutongwuyanzu/TaskHandoff/actions  

发到 [@tianyi 原帖](https://x.com/tianyi/status/2084693319188439211) 评论，并 **私信邮箱**。

---

## 评论区模板（复制即用）

```text
GitHub ID: sutongwuyanzu
项目: https://github.com/sutongwuyanzu/TaskHandoff
类型: Skill + CLI + MCP（同一 .handoff/ 契约）
版本: v0.2.6

一句话: DeepSeek 友好的「长任务交接 / 项目记忆 / 跨会话 handoff」。
状态写入仓库 .handoff/；新会话可用 recall --brief 恢复 goal 与结构化 next。

能力:
- handoff init/save/recall/status/doctor/memory
- MCP stdio（纯 stdlib）：handoff-mcp
- save --auto、hooks（SessionStart→recall / SessionEnd→save）
- 连续性证据（CI）: pytest tests/test_continuity.py -q
  说明: https://github.com/sutongwuyanzu/TaskHandoff/blob/main/examples/continuity-proof.md
  口径: 证明磁盘级状态恢复；LLM 执行质量需 harness 级评测

承诺: DSH 发布第一时间做 skill/MCP 适配与兼容验证
邮箱已私信，谢谢！
```

---

## 私信模板

```text
老师好，申请 DSH 内测。

项目: TaskHandoff v0.2.6
https://github.com/sutongwuyanzu/TaskHandoff
连续性说明: https://github.com/sutongwuyanzu/TaskHandoff/blob/main/examples/continuity-proof.md

类型: Skill + CLI + MCP（长任务交接 / 跨会话状态恢复）
GitHub: sutongwuyanzu
邮箱: <填你的邮箱>

我们证明的是 .handoff/ 磁盘级跨进程恢复；不声称 LLM 必完成任务。
希望 DSH 发布时第一时间接入，谢谢！
```

---

## 报名前检查清单

- [x] 公开仓库 + v0.2.6
- [x] CI green on `479f3bd`（v0.2.6）
- [x] 连续性格: `tests/test_continuity.py` 进 CI；文档 [examples/continuity-proof.md](examples/continuity-proof.md)
- [x] 口径: state recovery proven；LLM execution requires harness-level evaluation
- [x] wheel: templates 打进包，干净环境 init/save/recall 可用
- [ ] 评论报名 + 私信邮箱
