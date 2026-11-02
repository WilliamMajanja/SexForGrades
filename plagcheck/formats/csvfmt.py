from __future__ import annotations

from pathlib import Path

from ..core.registry import Format, Inspection


class CsvFormat(Format):
    name = "csv"
    description = "CSV/tabular text"
    extensions = [".csv", ".tsv"]

    def match(self, buf, size):
        s = bytes(buf)
        if b"," in s or b"\t" in s:
            # crude
            return 0.3
        return 0.0

    def inspect(self, path, buf, size):
        ins = Inspection(self.name, 0.8)
        ins.summary = "Delimited text"
        try:
            text = Path(path).read_text(errors="replace")
            lines = text.splitlines()
            ins.add_finding("stats", f"{len(lines)} lines")
        except Exception as e:
            ins.add_limit(f"read error: {e}")
        return ins
