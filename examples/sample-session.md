# Example: multi-day feature with handoff

## Day 1 — start

```bash
python scripts/handoff_cli.py init --root ~/code/my-app
```

Agent implements auth middleware. Before closing:

```bash
python scripts/handoff_cli.py save --root ~/code/my-app \
  --goal "Add JWT auth to API" \
  --done "Scaffold middleware and route guards" \
  --doing "Refresh-token flow" \
  --decision "Use httpOnly cookie for refresh token" \
  --file "src/auth/middleware.ts" \
  --file "src/auth/tokens.ts" \
  --next "Finish refresh-token endpoint" \
  --next "Add integration tests for 401/403" \
  --next "Document env vars in README" \
  --memory-delta "- Auth: refresh token in httpOnly cookie; access token in memory only"
```

## Day 2 — resume

```bash
python scripts/handoff_cli.py recall --root ~/code/my-app --budget 2500
```

Agent loads pack, restates next actions, continues from action 1.

## User one-liners (natural language)

| User says | Agent does |
|-----------|------------|
| 交接一下 | `save` with current goal/status |
| 接着做 | `recall` then execute next #1 |
| 记住我们用 pnpm | `memory --append` preference |
| handoff status | `status` |
