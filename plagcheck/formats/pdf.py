from __future__ import annotations

from pathlib import Path

from ..core.registry import Format, Inspection
from .. import extract


class PdfFormat(Format):
    name = "pdf"
    description = "PDF documents"
    extensions = [".pdf"]

    def match(self, buf, size):
        if bytes(buf)[:4] == b"%PDF":
            return 0.99
        return 0.0

    def inspect(self, path, buf, size):
        ins = Inspection(self.name, 0.99)
        ins.summary = "PDF document"
        try:
            text = extract.extract_text(path)
            ins.add_finding("extracted", f"{len(text)} chars extracted (best-effort)")
            if not text.strip():
                ins.add_limit("no text extracted (possibly scanned/image PDF)")
        except Exception as e:
            ins.add_limit(f"extract error: {e}")
        return ins
