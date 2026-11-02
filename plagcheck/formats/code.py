from __future__ import annotations

from pathlib import Path

from ..core.registry import Format, Inspection
from .. import forensics


class CodeFormat(Format):
    name = "code"
    description = "Source code (py, c, cpp, h, js, ts, java, go, rs)"
    extensions = [
        ".py",
        ".c",
        ".h",
        ".cpp",
        ".cc",
        ".cxx",
        ".hpp",
        ".js",
        ".mjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".go",
        ".rs",
        ".sh",
        ".sql",
    ]

    def match(self, buf, size):
        s = bytes(buf)
        if b"\x00" in s:
            return 0.0
        # look for common code patterns
        if any(k in s for k in (b"def ", b"function ", b"#include", b"class ", b"import ", b"package ")):
            return 0.6
        return 0.0

    def inspect(self, path, buf, size):
        ins = Inspection(self.name, 0.9)
        ins.summary = "Source code"
        try:
            text = Path(path).read_text(errors="replace")
        except Exception as e:
            ins.add_limit(f"read error: {e}")
            return ins
        ins.add_finding("stats", f"{len(text)} chars, {len(text.splitlines())} lines")
        for f in forensics.scan_text(text):
            ins.add_finding(f["kind"], f["detail"], evidence=f.get("evidence"))
        return ins
