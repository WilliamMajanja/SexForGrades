from __future__ import annotations

import json
from pathlib import Path

from ..core.registry import Format, Inspection


class JsonFormat(Format):
    name = "json"
    description = "JSON documents"
    extensions = [".json"]

    def match(self, buf, size):
        s = bytes(buf).strip()
        if not s:
            return 0.0
        if s[0:1] in (b"{", b"["):
            try:
                json.loads(s)
                return 0.95
            except Exception:
                return 0.2
        return 0.0

    def inspect(self, path, buf, size):
        ins = Inspection(self.name, 0.95)
        ins.summary = "JSON document"
        try:
            data = json.loads(Path(path).read_text(errors="replace"))
            if isinstance(data, dict):
                ins.add_finding("structure", f"object with {len(data)} keys")
            elif isinstance(data, list):
                ins.add_finding("structure", f"array with {len(data)} items")
            else:
                ins.add_finding("structure", f"type={type(data).__name__}")
        except Exception as e:
            ins.add_limit(f"json parse error: {e}")
        return ins
