"""Inspect student handbooks for contradictions, vague clauses, due process violations."""
from __future__ import annotations

import re
from pathlib import Path
from .. import extract


RED_FLAGS = [
    (r"may be discontinued|discontinued at.*discretion", "discretionary punishment - due process concern"),
    (r"without prior notice|summary", "summary action - fairness/due process concern"),
    (r"the.*committee.*decision.*final|final and binding", "ouster of appeal - natural justice concern"),
    (r"missing mark|result.*lost", "missing marks policy - compare to practice"),
    (r"sexual harassment", "sexual harassment policy - check enforcement mechanisms"),
    (r"fee.*balance.*examination|barred.*exam", "exam barring over fees - legality varies"),
    (r"appeal.*days|appeal.*period", "appeal timelines - may be unreasonably short"),
    (r"dean.*absolute|vice chancellor.*discretion", "excessive discretion - rule of law concern"),
]


class HandbookInspector:
    def inspect(self, path):
        text = extract.extract_text(path)
        findings = []
        for pat, reason in RED_FLAGS:
            for m in re.finditer(pat, text, re.I):
                start = max(0, m.start() - 80)
                end = min(len(text), m.end() + 80)
                findings.append({
                    "pattern": pat,
                    "reason": reason,
                    "snippet": text[start:end].replace("\n", " "),
                })
        return {
            "file": str(Path(path).resolve()),
            "chars": len(text),
            "red_flags": findings,
            "count": len(findings),
            "note": "For legal review - focus on contradictions with practice, natural justice, and constitutionality.",
        }

    def report(self, findings, outpath):
        import json
        from pathlib import Path
        Path(outpath).write_text(json.dumps(findings, indent=2))
        return findings
