# SexForGrades — Students Liberation Engine (SLE)

**A student-run, zero-dependency Students Liberation Engine built to question, audit and expose the legitimacy of tenured professorships across Kenya's public universities, private universities, and national polytechnics.**

SexForGrades is an evidence-first forensic toolkit. It equips students with the ability to verify academic credentials, publication records, supervision claims, and patterns of impunity using publicly verifiable documents. Everything runs locally, audibly, and with the bare minimum of data.

## The Kenyan Crisis

For decades, Kenya's higher education has been captured by impunity. Tenured professorships, associate professorships and senior academic posts have too often gone by patronage rather than merit. 

- **Missing marks as a weapon**: Results are delayed, "lost", or changed to force compliance.
- **Sex-for-grades & extortion**: Sexual favors and bribes are demanded to clear legitimately earned marks.
- **Victimisation**: Students who question are intimidated, gaslit with "respect your professor", or punished through the system.
- **Committee cover-ups**: Identical boilerplate responses are sent to multiple students year after year.

## Kenya Methodist University (KeMU) — A Case Study

At **Kenya Methodist University (KeMU)**, the author experienced this firsthand. Under heavy **GEMA** patronage influence whilst marketed as a Christian university:
- **Science suppression**: Pure sciences (Mathematics, Physics, Chemistry, Biology, Computer Science and related fields) face disproportionate missing marks, grade obstruction and bureaucratic runarounds.
- **Connected protected**: Patronage consistently shields the well-connected regardless of conduct or competence.
- **Bureaucratic gaslighting**: Complaints vanish into endless committees whilst graduation dates, scholarships and opportunities slip away.
- **Credential opacity**: Students are left in the dark about whether those grading them are actually qualified for the titles they hold.

## What SexForGrades Does

SexForGrades repurposes robust **winnowing fingerprinting (MOSS-style)** for accountability:

| Capability | Purpose |
|---|---|
| **Professor Qualification Audit** | Build a verifiable corpus of CVs, CUE/commission profiles, staff pages and public claims to cross-reference against evidence. |
| **Publication Forensics** | Detect duplicate/recycled publications, suspiciously similar abstracts, and boilerplate across "research". |
| **Thesis Supervision Mapping** | Cross-reference who claims to supervise in fields with no demonstrable expertise or verifiable track record. |
| **Missing Marks Ledger** | A student-driven, fact-based ledger of missing marks, extortion attempts, and follow-ups. Record dates, offices, names, responses — not just accusations. |
| **Cover-Up Pattern Detection** | Compare committee/department responses to expose identical copy-pasted letters used across cohorts. |
| **Forensic Inspection** | Detect tampering: zero-width characters (U+200B/C/D/U+2060), bidirectional marks, homoglyphs, mixed scripts and suspicious edits. |
| **Evidence Preservation** | Hash files (SHA256), maintain a timeline of events, and keep an auditable chain of evidence for petitions and legal action. |
| **Privacy-First by Design** | Runs 100% offline. No telemetry, no cloud sync, no exfiltration. You control your corpus. |

## API / CLI Reference

All commands are under the `sexforgrades` module/CLI:

```bash
# Identify & inspect documents forensics
python3 -m sexforgrades identify <file>
python3 -m sexforgrades inspect <file> --json
python3 -m sexforgrades list-formats

# Build and use evidence corpus
python3 -m sexforgrades index <corpus_dir> --out evidence.index.json
python3 -m sexforgrades check <submission> --corpus <dir> --html audit_report.html
python3 -m sexforgrades check <submission> --index evidence.index.json --json-out report.json

# Internal pattern detection (petitions/responses)
python3 -m sexforgrades internal <file> --json

# MCP server (stdio) for local tooling
python3 -m sexforgrades mcp
```

Programmatic API (Python):
```python
from sexforgrades import CorpusIndex, analyze, extract_text
from sexforgrades.core import registry
from sexforgrades import forensics

# Load evidence
ci = CorpusIndex()
ci.build("./corpus")

# Audit against evidence
res = analyze(extract_text("prof_cv.pdf"), ci)
print(res.similarity, res.source_hits)
```

## Quick Start (Hands On)

```bash
# 1) Collect public evidence (CVs, staff profiles, publications, committee letters, emails)
mkdir -p corpus

# 2) Build the evidence index
python3 -m sexforgrades index corpus --out sle.index.json

# 3) Audit a suspect CV or publication
python3 -m sexforgrades check suspect_cv.txt --index sle.index.json --html audit_report.html

# 4) Spot copy-pasted committee responses
python3 -m sexforgrades internal department_response.txt

# 5) Forensically inspect a suspicious letter/email
python3 -m sexforgrades inspect suspicious_letter.pdf --json
```

## Reporting Missing Marks & Sex-For-Grades (For Legal Action)

SexForGrades is designed to feed into legal class action. Document responsibly:

- **Facts only**: Date, time, office/department, person contacted, unit code, exact response received, witnesses (if any).
- **Evidence**: Save emails, SMS, result slips, fee receipts, official letters. Hash them locally.
- **Consent**: Only share with verified legal counsel (e.g. FIDA Kenya, Kituo Cha Sheria, KNCHR) with explicit consent.
- **Anonymise**: For public petitions, aggregate patterns without exposing identities unless consented.
- **Safety first**: If at immediate risk of retaliation, prioritise personal safety over documentation.

## Guiding Principles

- **Students First** — This engine belongs to students. Documentation, not harassment.
- **Evidence Over Hearsay** — Public records, official documents, emails, published papers, first-hand documented testimony.
- **Merit Over Patronage** — Restore academic merit and protect students in the sciences.
- **Transparency** — Open, auditable code. No hidden telemetry or data exfiltration.
- **Safety & Consent** — Privacy, minimisation, and informed consent are non-negotiable.
- **Liberation Through Knowledge** — Informed students are harder to gaslight.

## The Mission

**Question everything. Document everything. Verify everything.**

Every student deserves to know: *Is the person holding a professorial chair actually qualified for it? Does their body of work justify tenure? Or are they there by patronage whilst blocking others and extorting those beneath them?*

The era of blind reverence is over. The **Students Liberation Engine** exists to restore academic merit, end impunity, and fight for justice in Kenyan higher education.

*For every student bounced between offices at KeMU, UoN, KU, Moi, Egerton, JKUAT, Maseno, TUK, KPU, and every polytechnic fighting for their rightful marks. Solidarity with those currently protesting corrupt educators.*
