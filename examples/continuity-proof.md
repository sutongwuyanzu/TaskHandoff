# 续上证明：有什么、没有什么

## 一句话

**有「恢复契约」的硬证明：Session A 写入磁盘后，Session B 在无聊天历史时能读回 goal + next。**  
**还没有「任意 LLM 一定把活干完」的评测集**——那是模型执行力，不是 handoff 格式本身。

---

## 已有证据（可复现）

| 证据 | 位置 | 证明什么 |
|------|------|----------|
| 自动化测试 | `tests/test_continuity.py` | A 保存 → B recall，goal/next 完整 |
| 一键演示 | `python scripts/continuity_proof.py` | 终端打印 PASS/FAIL |
| 契约测试 | `tests/test_cli.py` | save/recall/doctor 管线 |
| Hook 生命周期 | `tests/test_hooks.py` | end save → start brief |
| 本仓库 dogfood | `.handoff/handoffs/LATEST.md` | 真实项目写过交接包 |

### 本地跑证明

```bash
pip install -e ".[dev]"
pytest tests/test_continuity.py -q
python scripts/continuity_proof.py
```

期望：`PASS — Session B recovered goal + all 3 next actions from disk alone.`

---

## 这证明了什么

```text
Session A  (有上下文)
   │  handoff save
   ▼
.handoff/  (磁盘，可 git)
   │  关闭聊天 / 换模型 / 换 harness
   ▼
Session B  (无历史)
   │  handoff recall --brief
   ▼
拿到：目标 + 下一步 1..3 + 关键决策/文件
```

即：**续上所需的「状态」不依赖会话记忆，而依赖仓库文件。**

---

## 这还没证明什么（诚实边界）

| 未证明 | 原因 |
|--------|------|
| Agent 一定会正确执行 next #1 | 取决于模型与 harness |
| 比「人肉写备忘录」更聪明 | 价值在结构化 + 可脚本/MCP/hooks |
| 生产级万人日任务 | 需真实项目长期 dogfood |

若要更强证明，下一步是：固定一个小任务，**Session A 做到一半强制断 → Session B 只喂 brief → 看能否完成**（人工或 agent eval 各跑 3 次）。

---

## 对外怎么说（报名/回复用）

> 我们不声称「模型更强」，而是证明：**交接状态落在 `.handoff/` 后，新会话无需聊天历史即可恢复 goal 与 next actions**（见 `tests/test_continuity.py` / `scripts/continuity_proof.py`）。
