"""Analyze Kenya education vs military spending using public data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class BudgetAnalyzer:
    def __init__(self):
        self.data = []

    def load(self, path):
        p = Path(path)
        if p.suffix == ".json":
            self.data = json.loads(p.read_text())
        elif p.suffix == ".csv":
            import csv

            with open(p) as f:
                self.data = list(csv.DictReader(f))
        return self

    def analyze_education_vs_defense(self):
        edu = 0.0
        defn = 0.0
        for row in self.data:
            sector = str(row.get("sector") or row.get("category") or "").lower()
            amt = float(row.get("amount") or row.get("budget") or row.get("allocation") or 0)
            if "educat" in sector or "university" in sector or "polytechnic" in sector:
                edu += amt
            elif "defen" in sector or "milit" in sector or "security" in sector:
                defn += amt
        return {
            "education_total": edu,
            "defense_security_total": defn,
            "ratio_edu_to_defense": (edu / defn) if defn else None,
            "summary": f"Education: {edu:,.0f}, Defense/Security: {defn:,.0f}",
        }

    def export_report(self, outpath):
        report = self.analyze_education_vs_defense()
        Path(outpath).write_text(json.dumps(report, indent=2))
        return report
