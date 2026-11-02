from __future__ import annotations

from pathlib import Path

from ..core.registry import Format, Inspection
from .. import extract


class DocxFormat(Format):
    name = "docx"
    description = "Microsoft Word OOXML (.docx)"
    extensions = [".docx"]

    def match(self, buf, size):
        s = bytes(buf)
        # zip magic
        if s[:2] == b"PK":
            # crude
            if b"word/" in s or b"[Content_Types].xml" in s:
                return 0.9
            return 0.3
        return 0.0

    def inspect(self, path, buf, size):
        ins = Inspection(self.name, 0.95)
        ins.summary = "DOCX document"
        try:
            text = extract.extract_text(path)
            ins.add_finding("extracted", f"{len(text)} chars extracted via stdlib")
        except Exception as e:
            ins.add_limit(f"extract error: {e}")
        return ins
