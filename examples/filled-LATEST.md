# Handoff Pack（示例：真实风格，供 README / 演示）

## Meta

- **Created**: 2026-08-05T02:00:00Z
- **Branch**: main @ a1b2c3d
- **Dirty**: 3 changed path(s): src/auth/middleware.ts, src/auth/tokens.ts, tests/auth.test.ts
- **Agent note**: task-handoff

## Goal

为 API 增加 JWT 鉴权（access + refresh），并保证 401/403 有集成测试。

## Status

### Done

- 脚手架：`src/auth/middleware.ts` 路由守卫
- access token 仅内存持有的约定写进 MEMORY

### Doing

- refresh-token 接口与 cookie 写出

### Blocked

- 等产品确认 refresh cookie 的 `SameSite` 策略（Lax vs None）

## Decisions

- refresh token 放 httpOnly cookie；access token 不进 localStorage
- 测试框架沿用 vitest（与现有仓库一致）

## Memory deltas

- Auth: refresh=httpOnly cookie；access=memory-only
- 包管理：本仓库固定 pnpm

## Artifacts

- **Key files**: src/auth/middleware.ts, src/auth/tokens.ts, tests/auth.test.ts
- **Commands**: `pnpm test tests/auth.test.ts`
- **Links / PRs**: (none yet)

## Open questions

- 生产环境 cookie Domain 是否要带子域？

## Next actions

1. 完成 `POST /auth/refresh` 与 cookie 设置
2. 补 401/403 集成测试并跑绿
3. README 增加 `AUTH_COOKIE_SAMESITE` 环境变量说明

## Resume prompt

```text
Continue this project from the handoff pack.
Goal: 为 API 增加 JWT 鉴权（access + refresh），并保证 401/403 有集成测试。
Next: 1) 完成 POST /auth/refresh 与 cookie 设置 2) 补 401/403 集成测试并跑绿 3) README 增加 AUTH_COOKIE_SAMESITE 说明
Read .handoff/MEMORY.md and .handoff/handoffs/LATEST.md first, then execute action 1.
```
