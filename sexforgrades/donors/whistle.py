"""Donor whistleblowing - track funding influence, conditions, conflicts of interest."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


class DonorTracker:
    def __init__(self, root="./donor_watch"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "reports").mkdir(exist_ok=True)
        (self.root / "evidence").mkdir(exist_ok=True)

    def hash_file(self, filepath):
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def report(self, donor_name, institution, details, evidence_files=None, conditions=None, conflict_of_interest=None):
        report_id = hashlib.sha256(f"{donor_name}{institution}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        entry = {
            "report_id": report_id,
            "donor_name": donor_name,
            "institution": institution,
            "conditions": conditions or [],
            "conflict_of_interest": conflict_of_interest or [],
            "details": details,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "evidence": [],
        }
        if evidence_files:
            for fp in evidence_files:
                fp = Path(fp)
                if fp.exists():
                    h = self.hash_file(fp)
                    entry["evidence"].append({"file": fp.name, "sha256": h})
        out = self.root / "reports" / f"{report_id}.json"
        out.write_text(json.dumps(entry, indent=2))
        return entry

    def aggregate(self):
        reports = []
        for f in (self.root / "reports").glob("*.json"):
            reports.append(json.loads(f.read_text()))
        return {"count": len(reports), "reports": reports}
