"""A small browser UI built on http.server (standard library only).

Run with:  python3 -m plagcheck serve --port 8000
Then open http://127.0.0.1:8000/
"""

from __future__ import annotations

import html
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .compare import analyze
from .extract import extract_bytes, fetch_url
from .index import build_index
from .report import render_html

_BOUNDARY_RE = re.compile(r'boundary="?([^";]+)"?', re.IGNORECASE)
MAX_UPLOAD = 20 * 1024 * 1024  # 20 MiB


def parse_urlencoded(body: bytes) -> dict[str, str]:
    parsed = urllib.parse.parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items()}


def parse_multipart(body: bytes, boundary: str) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    delimiter = b"--" + boundary.encode("utf-8", "replace")
    fields: dict[str, str] = {}
    files: dict[str, tuple[str, bytes]] = {}
    for chunk in body.split(delimiter):
        if not chunk or chunk in (b"--", b"--\r\n", b"\r\n"):
            continue
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]
        if chunk.endswith(b"\r\n"):
            chunk = chunk[:-2]
        if chunk.endswith(b"--"):
            chunk = chunk[:-2]
        header_blob, _, data = chunk.partition(b"\r\n\r\n")
        headers = header_blob.decode("utf-8", "replace")
        name_match = re.search(r'name="([^"]*)"', headers)
        if not name_match:
            continue
        name = name_match.group(1)
        filename_match = re.search(r'filename="([^"]*)"', headers)
        if filename_match and filename_match.group(1):
            files[name] = (filename_match.group(1), data)
        else:
            fields[name] = data.decode("utf-8", "replace")
    return fields, files


def _index_page(corpus_size: int, k: int, w: int, message: str = "") -> str:
    alert = f'<p class="alert">{html.escape(message)}</p>' if message else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>plagcheck</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f1f5f9; color: #0f172a; }}
  header {{ background: #0f172a; color: #fff; padding: 22px 28px; }}
  header h1 {{ margin: 0; font-size: 20px; }}
  header p {{ margin: 6px 0 0; color: #94a3b8; font-size: 13px; }}
  .wrap {{ max-width: 820px; margin: 28px auto; padding: 0 20px; }}
  .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; }}
  label {{ display: block; font-weight: 600; font-size: 13px; margin: 14px 0 6px; color: #334155; }}
  textarea {{ width: 100%; min-height: 180px; padding: 12px; border: 1px solid #cbd5e1;
             border-radius: 8px; font-size: 14px; font-family: inherit; resize: vertical; }}
  input[type=file] {{ font-size: 13px; }}
  .opts {{ display: flex; flex-wrap: wrap; gap: 16px; margin-top: 14px; font-size: 13px; color: #475569; }}
  .opts label {{ display: inline-flex; align-items: center; gap: 6px; margin: 0; font-weight: 500; }}
  button {{ margin-top: 20px; background: #2563eb; color: #fff; border: 0; border-radius: 8px;
           padding: 11px 22px; font-size: 14px; font-weight: 600; cursor: pointer; }}
  button:hover {{ background: #1d4ed8; }}
  .meta {{ font-size: 12px; color: #64748b; margin-top: 8px; }}
  .alert {{ background: #fef3c7; border: 1px solid #fcd34d; padding: 10px 14px; border-radius: 8px; font-size: 13px; }}
</style>
</head>
<body>
<header>
  <h1>plagcheck</h1>
  <p>Zero-dependency similarity checker &middot; {corpus_size} reference document(s) loaded &middot; match threshold &ge; {k + w - 1} words</p>
</header>
<div class="wrap">
  <form class="card" method="post" action="/check" enctype="multipart/form-data">
    {alert}
    <label for="text">Paste text</label>
    <textarea id="text" name="text" placeholder="Paste the document you want to check..."></textarea>
    <label for="file">Or upload a file (.txt, .md, .docx, .html, .pdf)</label>
    <input type="file" id="file" name="file" accept=".txt,.md,.markdown,.docx,.html,.htm,.pdf,.csv,.json">
    <label for="urls">Or add web sources (one URL per line, optional, needs internet)</label>
    <textarea id="urls" name="urls" style="min-height:70px" placeholder="https://example.com/article"></textarea>
    <div class="opts">
      <label><input type="checkbox" name="exclude_quotes" value="1"> Exclude quotes</label>
      <label><input type="checkbox" name="exclude_references" value="1"> Exclude references</label>
    </div>
    <button type="submit">Check similarity</button>
    <p class="meta">Privately processed on this machine. Nothing is uploaded to a third party.</p>
  </form>
</div>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    index = None
    k = 5
    w = 4
    server_version = "plagcheck/1.0"

    def log_message(self, fmt, *args):  # quieter logging
        pass

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            page = _index_page(self.index.source_count(), self.k, self.w)
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send(200, b"ok", "text/plain; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/check":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_UPLOAD:
            self._send(413, b"upload too large", "text/plain; charset=utf-8")
            return
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        fields: dict[str, str] = {}
        files: dict[str, tuple[str, bytes]] = {}
        if content_type.startswith("multipart/form-data"):
            match = _BOUNDARY_RE.search(content_type)
            if match:
                fields, files = parse_multipart(body, match.group(1))
        else:
            fields = parse_urlencoded(body)

        text = fields.get("text", "")
        filename = "pasted-text.txt"
        for _, (name, data) in files.items():
            if not data:
                continue
            try:
                text = extract_bytes(name, data)
                filename = name
            except Exception as error:  # noqa: BLE001
                page = _index_page(
                    self.index.source_count(), self.k, self.w,
                    f"Could not read {name}: {error}",
                )
                self._send(400, page.encode("utf-8"), "text/html; charset=utf-8")
                return
            break

        if not text.strip():
            page = _index_page(
                self.index.source_count(), self.k, self.w,
                "Please paste text or choose a file.",
            )
            self._send(400, page.encode("utf-8"), "text/html; charset=utf-8")
            return

        local_index = None
        urls = [line.strip() for line in fields.get("urls", "").splitlines() if line.strip()]
        if urls:
            local_index = build_index([])
            for url in urls:
                try:
                    local_index.add_document(f"url:{url}", url, fetch_url(url))
                except Exception:  # noqa: BLE001
                    continue

        result = analyze(
            text,
            self.index,
            exclude_quotes=bool(fields.get("exclude_quotes")),
            exclude_references=bool(fields.get("exclude_references")),
        )
        if local_index is not None:
            web_result = analyze(
                text,
                local_index,
                exclude_quotes=bool(fields.get("exclude_quotes")),
                exclude_references=bool(fields.get("exclude_references")),
            )
            result = _merge_results(result, web_result)

        page = render_html(result, title=f"Similarity report: {filename}")
        self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")


def _merge_results(base, extra):
    """Combine a corpus result and a web-source result, keeping the max score."""

    from .compare import Result

    combined_sources = {source.source_id: source for source in base.sources}
    for source in extra.sources:
        combined_sources[source.source_id] = source
    sources = sorted(combined_sources.values(), key=lambda hit: (-hit.matched_words, hit.source_id))
    runs = sorted(base.runs + extra.runs, key=lambda run: run.char_start)
    matched = max(base.matched_words, extra.matched_words)
    total = base.total_words or extra.total_words
    return Result(
        total_words=total,
        matched_words=matched,
        percent=(matched / total * 100.0) if total else 0.0,
        sources=sources,
        runs=runs,
        analyzed_text=base.analyzed_text,
        excluded_words=base.excluded_words,
        k=base.k,
        w=base.w,
        guarantee=base.guarantee,
    )


def serve(*, corpus: Path, host: str = "127.0.0.1", port: int = 8000, k: int = 5, w: int = 4) -> None:
    index = build_index([])
    if corpus.is_dir():
        from .cli import build_corpus_index

        index = build_corpus_index(corpus, k=k, w=w, exclude_quotes=False, exclude_references=False)
    Handler.index = index
    Handler.k = k
    Handler.w = w
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"plagcheck serving on http://{host}:{port}/  ({index.source_count()} sources)")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        server.server_close()
