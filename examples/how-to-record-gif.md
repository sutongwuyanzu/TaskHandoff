# 终端 GIF 怎么弄？

三种路线，从「最省事」到「最真实」。

---

## 方案 A（推荐本仓库）：脚本直接渲 GIF

不装 VHS / 不录屏，用 Pillow 生成终端风格动画：

```bash
cd TaskHandoff
pip install pillow          # 多数环境已有
python scripts/render_terminal_gif.py
# 输出: assets/terminal-demo.gif
```

README 已引用该图。改台词编辑 `scripts/render_terminal_gif.py` 里的 `SCENES` 再跑一遍即可。

**优点**：Windows 友好、可复现、CI 也能跑。  
**缺点**：是「仿终端画面」，不是真实 PTY 录像。

---

## 方案 B：本机录屏（最真实）

适合你想展示「真机命令」时。

### Windows

1. 开一个干净的 PowerShell / Windows Terminal（深色主题、字号大一点）。
2. 窗口缩到约 100×30，背景别太花。
3. 录制工具任选其一：
   - **[ScreenToGif](https://www.screentogif.com/)**（免费，可直接出 GIF，推荐）
   - Win + G 游戏栏录 MP4，再用 [ezgif.com](https://ezgif.com/video-to-gif) 转 GIF
4. 按 `examples/terminal-demo.md` 敲命令（可先写好再复制粘贴）。
5. 导出 GIF：
   - 宽度 800–1000px
   - 帧率 10–15fps
   - 控制在 **2MB 以内**（GitHub README 友好）
6. 存到 `assets/terminal-demo.gif` 覆盖即可。

### 演示脚本（录的时候跑）

```powershell
# 在 TaskHandoff 仓库
pip install -e .
$demo = Join-Path $env:TEMP "th-gif-demo"
Remove-Item -Recurse -Force $demo -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $demo | Out-Null
Set-Location $demo
Set-Content app.py "print('hi')"

handoff --version
handoff init --root .
handoff save --root . --auto `
  --goal "Ship JWT auth" `
  --done "Scaffold" `
  --next "Finish refresh" --next "Add tests" --next "Docs"
handoff recall --root . --brief
handoff doctor --root .
```

录制时每步之间停 0.5–1 秒，GIF 更清晰。

---

## 方案 C：VHS（真实终端 + 可复现）

[charmbracelet/vhs](https://github.com/charmbracelet/vhs) 用 `.tape` 脚本录真终端。

```bash
# 安装（任选其一）
# go install github.com/charmbracelet/vhs@latest
# scoop install vhs
# brew install vhs

cd TaskHandoff
vhs examples/demo.tape
# 按 tape 配置输出 GIF
```

本仓库提供了 [`examples/demo.tape`](demo.tape)。需要本机有 `ffmpeg` + `vhs`。

---

## README 引用方式

```markdown
![TaskHandoff terminal demo](assets/terminal-demo.gif)
```

## 尺寸建议

| 项 | 建议 |
|----|------|
| 宽 | 800–1000 px |
| 时长 | 8–15 秒 |
| 体积 | < 2 MB |
| 循环 | loop |
| 内容 | init → save → recall → doctor |
