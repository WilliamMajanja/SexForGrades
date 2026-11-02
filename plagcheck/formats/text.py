from __future__ import annotations

from pathlib import Path

from ..core.registry import Format, Inspection
from .. import forensics


class TextFormat(Format):
    name = "text"
    description = "Plain text documents (.txt, .md, .rst, .log)"
    confidence = 0.9
    extensions = [".txt", ".md", ".rst", ".log", ".text"]

    def match(self, buf, size):
        s = bytes(buf)
        if not s:
            return 0.1
        # binary check
        if b"\x00" in s:
            return 0.0
        ext = None  # match can be called without path; rely on inspect for ext mostly
        # try to be permissive - text is fallback
        # high confidence if no null bytes and mostly printable
        printable = sum(1 for b in s if 32 <= b < 127 or b in (9, 10, 13))
        if size and printable / min(size, len(s)) > 0.7:
            return 0.4
        return 0.1

    def inspect(self, path, buf, size):
        p = Path(path)
        ins = Inspection(self.name, 0.9)
        ins.summary = "Plain text document"
        try:
            text = Path(path).read_text(errors="replace")
        except Exception as e:
            ins.add_limit(f"read error: {e}")
            return ins

        ins.add_finding("stats", f"{len(text)} chars, {len(text.split())} words")
        # forensics
        fw = forensics.scan_text(text)
        for f in fw:
            ins.add_finding(f["kind"], f["detail"], evidence=f.get("evidence"))
        if fw:
            ins.summary = f"Plain text with {len(fw)} forensics findings"
        return ins
