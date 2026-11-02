"""Aggregate patterns without exposing identities."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


class AggregateDashboard:
    def __init__(self):
        self.reports = []

    def load(self, path):
        data = json.loads(Path(path).read_text())
        if isinstance(data, list):
            self.reports = data
        else:
            self.reports = [data]
        return self

    def aggregate_missing_marks(self):
        by_institution = Counter()
        by_year = Counter()
        by_course = Counter()
        for r in self.reports:
            if r.get("type") == "missing_marks":
                by_institution[r.get("institution", "unknown")] += 1
                by_year[r.get("academic_year", "unknown")] += 1
                by_course[r.get("course", "unknown")] += 1
        return {
            "by_institution": dict(by_institution),
            "by_year": dict(by_year),
            "by_course": dict(by_course),
            "total": len([r for r in self.reports if r.get("type") == "missing_marks"]),
        }

    def aggregate_science_suppression(self):
        sciences = {"mathematics", "physics", "chemistry", "biology", "computer science", "statistics"}
        count = 0
        for r in self.reports:
            c = str(r.get("course", "")).lower()
            if any(s in c for s in sciences):
                if r.get("type") in ("missing_marks", "delayed_results", "victimization"):
                    count += 1
        return {"science_related_complaints": count}

    def export(self, outpath):
        report = {
            "missing_marks": self.aggregate_missing_marks(),
            "science_suppression": self.aggregate_science_suppression(),
        }
        Path(outpath).write_text(json.dumps(report, indent=2))
        return report
