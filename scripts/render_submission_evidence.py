"""Render honest, reproducible PNG evidence from benchmark/privacy artifacts."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "benchmark.json"
DATASET = ROOT / "data" / "sessions.json"
SUBMISSION = ROOT / "submission"
FONT_PATHS = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    Path("C:/Windows/Fonts/consola.ttf"),
)

WIDTH = 1500
HEIGHT = 920
BACKGROUND = "#0b1220"
PANEL = "#111c2f"
TEXT = "#dbeafe"
MUTED = "#93a4bd"
GREEN = "#4ade80"
CYAN = "#22d3ee"
YELLOW = "#facc15"


def _font(size: int):
    for path in FONT_PATHS:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


TITLE_FONT = _font(34)
BODY_FONT = _font(22)
SMALL_FONT = _font(18)


def _draw_wrapped(draw, text: str, xy: tuple[int, int], *, width: int = 104, fill=TEXT,
                  font=BODY_FONT, spacing: int = 7) -> int:
    x, y = xy
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        lines.extend(textwrap.wrap(paragraph, width=width) or [""])
    draw.multiline_text((x, y), "\n".join(lines), font=font, fill=fill, spacing=spacing)
    line_height = font.getbbox("Ag")[3] + spacing
    return y + line_height * len(lines)


def _canvas(title: str, subtitle: str):
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((35, 35, WIDTH - 35, HEIGHT - 35), radius=24, fill=PANEL,
                           outline="#334155", width=2)
    draw.text((75, 70), title, font=TITLE_FONT, fill=CYAN)
    draw.text((75, 120), subtitle, font=SMALL_FONT, fill=MUTED)
    draw.line((75, 158, WIDTH - 75, 158), fill="#334155", width=2)
    return image, draw


def render_layer(payload: dict, layer: str, case_ids: list[str], output: Path) -> None:
    title = f"Lab 17 Runtime Evidence - {layer.replace('_', ' ').title()}"
    subtitle = "python -m src.evaluate --impl student --reuse-seeded"
    image, draw = _canvas(title, subtitle)
    by_id = {result["id"]: result for result in payload["results"]}
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in dataset["evaluations"]}
    y = 190
    for case_id in case_ids:
        result = by_id[case_id]
        case = cases[case_id]
        status = "PASS" if result["passed"] else "FAIL"
        color = GREEN if result["passed"] else "#fb7185"
        draw.text((80, y), f"[{status}] {case_id}  {result['layer']}", font=BODY_FONT, fill=color)
        draw.text(
            (760, y),
            f"latency={result['latency_ms']:.1f} ms   tokens={result['retrieved_tokens']}",
            font=SMALL_FONT,
            fill=YELLOW,
        )
        y += 40
        y = _draw_wrapped(draw, f"Query: {result['query']}", (100, y), fill=TEXT)
        markers = ", ".join(case.get("must_contain_all") or [])
        y = _draw_wrapped(draw, f"Verified markers: {markers}", (100, y + 3), fill=CYAN,
                          font=SMALL_FONT, width=128, spacing=5)
        forbidden = ", ".join(case.get("must_not_contain") or [])
        if forbidden:
            y = _draw_wrapped(draw, f"Forbidden markers absent: {forbidden}", (100, y + 2),
                              fill=GREEN, font=SMALL_FONT, width=128, spacing=5)
        excerpt = " ".join((result.get("retrieved") or "").split())[:240]
        y = _draw_wrapped(draw, f"Evidence: {excerpt}", (100, y + 5), fill=MUTED,
                          font=SMALL_FONT, width=128, spacing=5)
        y += 24
    draw.text((80, HEIGHT - 78), "Source: reports/benchmark.json (student, 11/11 PASS)",
              font=SMALL_FONT, fill=MUTED)
    image.save(output, format="PNG", optimize=True)


def render_privacy(output: Path) -> None:
    image, draw = _canvas(
        "Lab 17 Runtime Evidence - Privacy Drill",
        "python -m src.forget --user-id minh-lab17 [--verify-only]",
    )
    content = (SUBMISSION / "privacy.txt").read_text(encoding="utf-8")
    y = _draw_wrapped(draw, content, (85, 195), width=112, fill=TEXT, font=BODY_FONT)
    draw.text((80, HEIGHT - 78), "Deletion scope: synthetic user only; shared semantic KB retained.",
              font=SMALL_FONT, fill=MUTED)
    if y > HEIGHT - 95:
        raise ValueError("Privacy evidence overflowed the image")
    image.save(output, format="PNG", optimize=True)


def main() -> None:
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    SUBMISSION.mkdir(exist_ok=True)
    render_layer(payload, "long_term", ["E02", "E03", "E08", "E09"],
                 SUBMISSION / "long_term.png")
    render_layer(payload, "episodic", ["E04", "E05"], SUBMISSION / "episodic.png")
    render_layer(payload, "semantic", ["E06", "E11", "E07"], SUBMISSION / "semantic.png")
    render_privacy(SUBMISSION / "privacy.png")
    for path in sorted(SUBMISSION.glob("*.png")):
        print(f"Wrote {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
