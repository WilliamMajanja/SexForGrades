from __future__ import annotations

from pathlib import Path

from ..core.registry import Format, Inspection
from .. import forensics


class HtmlFormat(Format):
    name = "html"
    description = "HTML documents (.html, .htm)"
    extensions = [".html", ".htm"]

    def match(self, buf, size):
        s = bytes(buf).lower()
        if b"<html" in s or b"<!doctype html" in s or (b"<head" in s and b"<body" in s):
            return 0.99
        if s.strip().startswith(b"<"):
            return 0.3
        return 0.0

    def inspect(self, path, buf, size):
        ins = Inspection(self.name, 0.99)
        ins.summary = "HTML document"
        try:
            text = Path(path).read_text(errors="replace")
        except Exception as e:
            ins.add_limit(f"read error: {e}")
            return ins
        ins.add_finding("stats", f"{len(text)} chars")
        for f in forensics.scan_text(text):
            ins.add_finding(f["kind"], f["detail"], evidence=f.get("evidence"))
        return ins
