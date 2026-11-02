"""Campaign tools - focus on systems, not individuals."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class Campaign:
    def __init__(self, root="./campaigns"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create_campaign(self, name, demands, targets=None):
        cid = name.lower().replace(" ", "_")
        camp = {"id": cid, "name": name, "demands": demands, "targets": targets or ["systemic"], "created": datetime.utcnow().isoformat() + "Z", "actions": [], "solidarity": []}
        (self.root / f"{cid}.json").write_text(json.dumps(camp, indent=2))
        return camp

    def add_action(self, cid, action_type, description):
        path = self.root / f"{cid}.json"
        camp = json.loads(path.read_text())
        camp["actions"].append({"type": action_type, "description": description, "time": datetime.utcnow().isoformat() + "Z"})
        path.write_text(json.dumps(camp, indent=2))
        return camp

    def mass_petition(self, demands, institution):
        from ..policy import petition
        pg = petition.PetitionGenerator()
        base = pg.generate_missing_marks_petition(institution) if institution else pg.generate_education_funding_petition()
        return base + "\n\nADDITIONAL DEMANDS (Mass Line):\n" + "\n".join(f"- {d}" for d in demands)
