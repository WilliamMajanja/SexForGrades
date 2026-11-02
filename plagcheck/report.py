"""Report rendering: HTML, JSON and plain text."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from .compare import Result

PALETTE = [
    "#fde68a",
    "#bfdbfe",
    "#fecaca",
    "#bbf7d0",
    "#e9d5ff",
    "#fed7aa",
    "#a5f3fc",
    "#f5d0fe",
    "#d9f99d",
    "#fbcfe8",
]

BAND_COLORS = {
    "low": "#16a34a",
    "moderate": "#ca8a04",
    "high": "#ea580c",
    "very high": "#dc2626",
}


def _color_map(result: Result) -> dict[str, tuple[int, str]]:
    mapping: dict[str, tuple[int, str]] = {}
    for position, source in enumerate(result.sources):
        mapping[source.source_id] = (position + 1, PALETTE[position % len(PALETTE)])
    return mapping


def render_highlighted_html(text: str, result: Result) -> str:
    """Return *text* as HTML with matched runs wrapped in <mark> spans."""

    colors = _color_map(result)
    pieces: list[str] = []
    cursor = 0
    for index, run in enumerate(result.runs):
        if run.char_start < cursor:
            continue
        pieces.append(html.escape(text[cursor : run.char_start]))
        primary = run.sources[0] if run.sources else ""
        number, color = colors.get(primary, (0, "#fde68a"))
        label = ", ".join(
            result_source_title(result, source_id) for source_id in run.sources
        )
        pieces.append(
            f'<mark class="hit" id="run-{index}" '
            f'style="background:{color}" '
            f'data-sources="{html.escape(label)}" '
            f'title="Source: {html.escape(label)}">'
            f'<span class="tag">{number}</span>{html.escape(text[run.char_start:run.char_end])}'
            f"</mark>"
        )
        cursor = run.char_end
    pieces.append(html.escape(text[cursor:]))
    return "".join(pieces)


def result_source_title(result: Result, source_id: str) -> str:
    for source in result.sources:
        if source.source_id == source_id:
            return source.title
    return source_id


def render_html(result: Result, *, title: str = "Similarity report") -> str:
    colors = _color_map(result)
    band_color = BAND_COLORS.get(result.score_band, "#334155")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows = []
    for source in result.sources:
        number, color = colors.get(source.source_id, (0, "#fde68a"))
        rows.append(
            "<tr>"
            f'<td><span class="chip" style="background:{color}">{number}</span></td>'
            f"<td>{html.escape(source.title)}</td>"
            f'<td class="num">{source.matched_words}</td>'
            f'<td class="num">{source.percent:.1f}%</td>'
            f'<td class="num">{len(source.matches)}</td>'
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="5" class="muted">No matching sources found.</td></tr>')

    body = render_highlighted_html(result.analyzed_text, result)
    band = result.score_band

    legend_items = []
    for source in result.sources:
        number, color = colors.get(source.source_id, (0, "#fde68a"))
        legend_items.append(
            f'<span><span class="chip" style="background:{color}">{number}</span>'
            f"{html.escape(source.title)}</span>"
        )
    legend = "".join(legend_items)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f1f5f9; color: #0f172a; }}
  header {{ background: #0f172a; color: #fff; padding: 20px 28px; }}
  header h1 {{ margin: 0; font-size: 18px; letter-spacing: .2px; }}
  header p {{ margin: 4px 0 0; color: #94a3b8; font-size: 13px; }}
  .wrap {{ max-width: 1100px; margin: 24px auto; padding: 0 20px; }}
  .grid {{ display: grid; grid-template-columns: 260px 1fr; gap: 20px; }}
  @media (max-width: 820px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; }}
  .score {{ font-size: 52px; font-weight: 700; line-height: 1; color: {band_color}; }}
  .band {{ display: inline-block; margin-top: 8px; padding: 3px 12px; border-radius: 999px;
          background: {band_color}; color: #fff; font-size: 12px; text-transform: uppercase;
          letter-spacing: .6px; }}
  .stats {{ margin-top: 16px; font-size: 13px; color: #475569; }}
  .stats div {{ display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #e2e8f0; }}
  h2 {{ font-size: 14px; text-transform: uppercase; letter-spacing: .6px; color: #475569; margin: 0 0 12px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
  th {{ color: #64748b; font-weight: 600; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .chip {{ display: inline-block; min-width: 20px; text-align: center; border-radius: 6px;
          padding: 1px 6px; font-size: 12px; font-weight: 600; }}
  .muted {{ color: #94a3b8; }}
  .doc {{ white-space: pre-wrap; line-height: 1.75; font-size: 15px; }}
  mark.hit {{ position: relative; border-radius: 3px; padding: 1px 0; box-shadow: inset 0 -2px 0 rgba(0,0,0,.06); }}
  mark.hit .tag {{ font-size: 9px; vertical-align: super; color: #334155; font-weight: 700; margin-right: 1px; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 12px; margin-top: 12px; }}
  .legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
  .note {{ font-size: 12px; color: #64748b; margin-top: 16px; }}
</style>
</head>
<body>
<header>
  <h1>{html.escape(title)}</h1>
  <p>Zero-dependency similarity analysis &middot; generated {generated}</p>
</header>
<div class="wrap">
  <div class="grid">
    <div>
      <div class="card">
        <h2>Similarity</h2>
        <div class="score">{result.percent:.0f}%</div>
        <span class="band">{band}</span>
        <div class="stats">
          <div><span>Words analysed</span><strong>{result.total_words}</strong></div>
          <div><span>Matching words</span><strong>{result.matched_words}</strong></div>
          <div><span>Matching sources</span><strong>{len(result.sources)}</strong></div>
          <div><span>Excluded words</span><strong>{result.excluded_words}</strong></div>
          <div><span>Match length</span><strong>&ge; {result.guarantee} words</strong></div>
        </div>
      </div>
      <div class="card" style="margin-top:20px">
        <h2>Sources</h2>
        <table>
          <thead><tr><th></th><th>Source</th><th class="num">Words</th><th class="num">%</th><th class="num">Hits</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <h2>Submitted document</h2>
      <div class="doc">{body}</div>
      <div class="legend">{legend}</div>
      <p class="note">Highlighting marks passages of at least {result.guarantee} consecutive words shared with a source.
      A percentage is a signal for review, not proof of plagiarism. Check quotation, citation and common-knowledge context manually.</p>
    </div>
  </div>
</div>
</body>
</html>
"""


def render_json(result: Result, *, meta: dict | None = None) -> str:
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "generator": "plagcheck",
    }
    if meta:
        payload.update(meta)
    payload["result"] = result.to_dict()
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_text(result: Result) -> str:
    lines = [
        f"Similarity: {result.percent:.1f}% ({result.score_band})",
        f"Words analysed: {result.total_words}",
        f"Matching words: {result.matched_words}",
        f"Excluded words: {result.excluded_words}",
        "",
        "Sources:",
    ]
    if result.sources:
        for source in result.sources:
            lines.append(
                f"  {source.percent:5.1f}%  {source.title}  "
                f"({source.matched_words} words, {len(source.matches)} hits)"
            )
    else:
        lines.append("  none")
    lines.append("")
    lines.append("Matched passages:")
    for run in result.runs:
        snippet = " ".join(run.text.split())
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        lines.append(f"  [{run.words}w] {snippet}")
    return "\n".join(lines)
