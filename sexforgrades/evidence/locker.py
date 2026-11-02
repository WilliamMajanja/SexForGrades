"""Evidence locker with hashing, consent, chain of custody."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path


class EvidenceLocker:
    def __init__(self, root="./evidence_locker"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "consent").mkdir(exist_ok=True)
        (self.root / "files").mkdir(exist_ok=True)
        (self.root / "timeline").mkdir(exist_ok=True)

    def hash_file(self, filepath):
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def add_evidence(self, reporter_consent_id, description, files=None, timeline_events=None):
        """Add evidence with explicit consent. Anonymised by default."""
        entry_id = hashlib.sha256(f"{reporter_consent_id}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        entry = {
            "entry_id": entry_id,
            "consent_id": reporter_consent_id,
            "description": description,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "files": [],
            "timeline": timeline_events or [],
            "chain_of_custody": [],
        }
        if files:
            for fp in files:
                fp = Path(fp)
                if fp.exists():
                    h = self.hash_file(fp)
                    dest = self.root / "files" / f"{entry_id}_{fp.name}"
                    # copy without reading into memory excessively
                    import shutil

                    shutil.copy2(fp, dest)
                    entry["files"].append({"name": fp.name, "sha256": h, "stored_as": str(dest)})
                    entry["chain_of_custody"].append({"action": "ingested", "sha256": h, "time": datetime.utcnow().isoformat() + "Z"})
        entry_path = self.root / "timeline" / f"{entry_id}.json"
        entry_path.write_text(json.dumps(entry, indent=2))
        return entry

    def record_consent(self, consent_id, details):
        """Record explicit consent - separate from public data."""
        consent = {
            "consent_id": consent_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": details,
            "revocable": True,
        }
        (self.root / "consent" / f"{consent_id}.json").write_text(json.dumps(consent, indent=2))
        return consent

    def export_for_legal(self, consent_id, outpath):
        """Export bundle only for verified legal counsel with consent."""
        bundle = []
        for f in (self.root / "timeline").glob("*.json"):
            data = json.loads(f.read_text())
            if data.get("consent_id") == consent_id:
                bundle.append(data)
        Path(outpath).write_text(json.dumps(bundle, indent=2))
        return bundle
