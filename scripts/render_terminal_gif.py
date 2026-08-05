#!/usr/bin/env python3
"""Render a terminal-style demo GIF for the README (no VHS required).

Usage:
  pip install pillow   # already common
  python scripts/render_terminal_gif.py
  # → assets/terminal-demo.gif

This is a *stylized* terminal recording (reliable on Windows CI/dev).
For a real PTY capture, see examples/how-to-record-gif.md
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:  # pragma: no cover
    raise SystemExit("Need Pillow: pip install pillow") from e

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "terminal-demo.gif"

# Scene: (delay_ms after frame, lines to show cumulatively added as new block)
# We rebuild frames as progressive terminal output.
SCENES: List[Tuple[int, List[str]]] = [
    (
        900,
        [
            "$ handoff --version",
            "handoff 0.2.2",
            "",
        ],
    ),
    (
        1100,
        [
            "$ handoff init --root .",
            "Initialized TaskHandoff at: ./.handoff",
            'Next: work on your task, then run `handoff save --auto`',
            "",
        ],
    ),
    (
        1400,
        [
            "$ handoff save --root . --auto \\",
            '    --goal "Ship JWT auth" \\',
            '    --next "Finish refresh" --next "Add tests" --next "Docs"',
            "Saved handoff: .handoff/handoffs/LATEST.md",
            "Goal:          Ship JWT auth",
            "Next actions:",
            "  1. Finish refresh",
            "  2. Add tests",
            "  3. Docs",
            "(auto mode: filled from git + previous handoff)",
            "",
        ],
    ),
    (
        1500,
        [
            "$ handoff recall --root . --brief",
            "# Resume brief (TaskHandoff)",
            "- project: `demo-app`",
            "- goal: Ship JWT auth",
            "- next:",
            "  1. Finish refresh",
            "  2. Add tests",
            "  3. Docs",
            "- instruction: Execute next action #1 now.",
            "",
        ],
    ),
    (
        1600,
        [
            "$ handoff doctor --root .",
            "doctor: ./demo-app",
            "  config.json: ok",
            "  MEMORY.md: ok",
            "  LATEST.md secret scan: clean",
            "result: OK",
            "",
            "# ✓ long tasks survive session resets",
        ],
    ),
]


def load_font(size: int = 16):
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
        "C:/Windows/Fonts/lucon.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def measure(draw: ImageDraw.ImageDraw, text: str, font) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def render_frames(
    scenes: Sequence[Tuple[int, List[str]]],
    *,
    width: int = 880,
    line_h: int = 22,
    pad: int = 18,
    bg: Tuple[int, int, int] = (18, 18, 24),
    fg: Tuple[int, int, int] = (220, 223, 228),
    prompt: Tuple[int, int, int] = (80, 200, 120),
    dim: Tuple[int, int, int] = (140, 150, 160),
    accent: Tuple[int, int, int] = (120, 180, 255),
    ok: Tuple[int, int, int] = (100, 220, 140),
) -> Tuple[List[Image.Image], List[int]]:
    font = load_font(15)
    title_font = load_font(13)

    lines: List[str] = []
    frames: List[Image.Image] = []
    durations: List[int] = []

    # title bar height
    chrome = 36

    for delay, block in scenes:
        lines.extend(block)
        # keep last N lines for frame height stability
        visible = lines[-22:]
        height = chrome + pad * 2 + line_h * max(len(visible), 12)
        img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(img)

        # window chrome
        draw.rectangle((0, 0, width, chrome), fill=(32, 34, 42))
        for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            x = 14 + i * 16
            draw.ellipse((x, 12, x + 10, 22), fill=color)
        draw.text((70, 10), "taskhandoff — terminal demo", font=title_font, fill=dim)

        y = chrome + pad
        for line in visible:
            color = fg
            if line.startswith("$"):
                color = prompt
            elif line.startswith("# Resume") or line.startswith("# ✓"):
                color = ok
            elif line.startswith("Goal:") or line.startswith("result:"):
                color = accent
            elif line.startswith("  ") and line.strip()[:1].isdigit():
                color = accent
            draw.text((pad, y), line, font=font, fill=color)
            y += line_h

        # caret blink on last prompt-ish frame
        caret_y = y - line_h if visible else chrome + pad
        draw.rectangle((pad, caret_y + 2, pad + 8, caret_y + line_h - 4), fill=prompt)

        frames.append(img)
        durations.append(delay)

    # hold last frame longer
    if durations:
        durations[-1] = max(durations[-1], 2200)
    return frames, durations


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames, durations = render_frames(SCENES)
    # normalize size to max frame
    max_w = max(f.size[0] for f in frames)
    max_h = max(f.size[1] for f in frames)
    norm: List[Image.Image] = []
    for f in frames:
        canvas = Image.new("RGB", (max_w, max_h), (18, 18, 24))
        canvas.paste(f, (0, 0))
        norm.append(canvas)

    norm[0].save(
        OUT,
        save_all=True,
        append_images=norm[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    size_kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT} ({size_kb:.1f} KB, {len(norm)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
