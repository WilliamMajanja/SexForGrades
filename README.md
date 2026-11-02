# SexForGrades — Students Liberation Engine (SLE)

**A student-run, zero-dependency Students Liberation Engine forged in the spirit of Marxist-Leninist-Maoist expressionism. Built to question, audit and expose the legitimacy of tenured professorships across Kenya's public universities, private universities, and national polytechnics.**

SexForGrades is an evidence-first forensic toolkit. It arms students with the means to verify academic credentials, publication records, supervision claims, and patterns of class-based impunity using publicly verifiable documents. Everything runs locally, auditable, and with the bare minimum of data.

## Historical & Material Context

Kenya's higher education is not neutral. It is a product of colonial residue, comprador bourgeois class reproduction, and neo-colonial structural adjustment. The university has been captured to serve the interests of the ruling comprador class and their imperialist patrons rather than the masses of working students. 

- **Missing marks as class warfare**: Results are deliberately delayed, "lost", or changed to discipline students and extort concessions.
- **Sex-for-grades & extortion**: Sexual favors and bribes are demanded as instruments of patriarchal domination and class control.
- **Victimisation of the masses**: Students who dare to resist are intimidated, gaslit with "respect your professor", or crushed through bureaucratic violence.
- **Committee cover-ups**: Identical boilerplate responses expose a coordinated class defence of the petty-bourgeois academic clique.
- **Science suppression**: Particularly at institutions like **Kenya Methodist University (KeMU)** under **GEMA** patronage networks, the pure sciences are sabotaged whilst theology and "safe" courses are propped up to reproduce a docile, conformist intelligentsia.

## Marxist-Leninist-Maoist Expressionism

This project draws inspiration from the revolutionary tradition of exposing bourgeois ideology within institutions of learning. Like the mass line, it trusts the masses of students to investigate, document, and expose. Like Maoist mass criticism, it weaponises facts and evidence to shatter illusions of neutrality. 

The struggle for academic merit is inseparable from the struggle against patronage, imperialism, gender oppression, and class exploitation. To question a professorial chair on the basis of merit is to question the entire structure of reproduction it upholds.

## Kenya Methodist University (KeMU) — A Case Study

Under the guise of a "Christian university" whilst deeply enmeshed in **GEMA** patronage:
- **Suppression of the sciences**: Mathematics, Physics, Chemistry, Biology, Computer Science and technical fields face disproportionate missing marks, grade obstruction and bureaucratic runarounds.
- **Patronage over merit**: The connected are shielded regardless of competence or predatory conduct.
- **Weaponised bureaucracy**: Endless committees bury complaints whilst graduation dates, scholarships and opportunities are stolen from students.
- **Credential opacity**: The masses have no right to know if those who grade and lecture them are qualified to hold the titles they brandish.

## What SexForGrades Does

SexForGrades repurposes robust **winnowing fingerprinting (MOSS-style)** for mass accountability:

| Capability | Purpose |
|---|---|
| **Professor Qualification Audit** | Build a verifiable mass corpus of CVs, CUE/commission profiles, staff pages and public claims to expose those lacking credentials for tenured posts. |
| **Publication Forensics** | Detect duplicate/recycled publications, suspiciously similar abstracts, and boilerplate across "research" used to justify tenure by patronage. |
| **Thesis Supervision Mapping** | Cross-reference predatory or unqualified supervisors who claim expertise they do not possess. |
| **Missing Marks Ledger** | A student-driven, fact-based mass ledger of missing marks, extortion attempts, and follow-ups. Record dates, offices, unit codes, responses — concrete facts for mass action. |
| **Cover-Up Pattern Detection** | Expose identical copy-pasted committee/department responses sent to cohorts across years as proof of coordinated class defence. |
| **Forensic Inspection** | Detect tampering: zero-width characters (U+200B/C/D/U+2060), bidirectional marks, homoglyphs, mixed scripts and suspicious edits. |
| **Evidence Preservation** | Hash files (SHA256), maintain a timeline of events, and preserve auditable evidence for petitions, mass campaigns and legal action. |
| **Privacy-First by Design** | Runs 100% offline. No telemetry, no cloud sync, no exlexfiltration. The masses control their own corpus. |

## API / CLI Reference

```bash
# Identify & inspect documents forensics
python3 -m sexforgrades identify <file>
python3 -m sexforgrades inspect <file> --json
python3 -m sexforgrades list-formats

# Build and use mass evidence corpus
python3 -m sexforgrades index <corpus_dir> --out sle.index.json
python3 -m sexforgrades check <submission> --corpus <dir> --html audit_report.html
python3 -m sexforgrades check <submission> --index sle.index.json --json-out report.json

# Internal pattern detection (petitions/cover-up responses)
python3 -m sexforgrades internal <file> --json

# Policy, rights, dashboard & consent-based evidence locker
python3 -m sexforgrades budget --input budget.csv --json
python3 -m sexforgrades petition --type education
python3 -m sexforgrades rights --json
python3 -m sexforgrades dashboard --input aggregates.json --out dashboard.json
python3 -m sexforgrades evidence-add --consent <id> --desc "..." --file evidence.pdf --json
python3 -m sexforgrades evidence-export --consent <id> --out bundle.json

# MCP server (stdio)
python3 -m sexforgrades mcp
```

Programmatic API:
```python
from sexforgrades import CorpusIndex, analyze, extract_text
from sexforgrades.core import registry
from sexforgrades import forensics
from sexforgrades.policy import budget, petition, civic
from sexforgrades.dashboard import aggregator
from sexforgrades.evidence import locker

ci = CorpusIndex(); ci.build("./corpus")
res = analyze(extract_text("prof_cv.pdf"), ci)
print(res.similarity, res.source_hits)
```

## Reporting Missing Marks & Sex-For-Grades (For Mass Action & Legal Action)

- **Facts only**: Date, time, office/department, person contacted, unit code, exact response received, witnesses (if any).
- **Evidence**: Save emails, SMS, result slips, fee receipts, official letters. Hash them locally.
- **Consent**: Only share with verified legal counsel (e.g. FIDA Kenya, Kituo Cha Sheria, KNCHR) with explicit consent.
- **Anonymise**: For mass petitions, aggregate patterns without exposing identities unless consented.
- **Safety first**: If at immediate risk of retaliation, prioritise personal safety over documentation.
- **Mass line**: Share aggregate findings with the student masses to build collective power.

## Guiding Principles

- **Students First** — The engine belongs to the masses of students. Documentation for liberation, not harassment.
- **Class Analysis** — Patronage, gender oppression and imperialism are material realities, not isolated incidents.
- **Evidence Over Hearsay** — Public records, official documents, emails, published papers, first-hand documented testimony.
- **Merit Over Patronage** — Restore academic merit and protect students in the sciences.
- **Mass Line** — From the masses, to the masses. Investigate collectively, expose collectively, struggle collectively.
- **Transparency & Auditable** — Open, auditable code. No hidden telemetry or data exfiltration.
- **Safety & Consent** — Privacy, minimisation, and informed consent are non-negotiable.
- **Liberation Through Knowledge** — Consciousness leads to struggle. Struggle leads to liberation.

## The Mission

**Question everything. Document everything. Verify everything. Unite to struggle.**

Every student deserves to know: *Is the person holding a professorial chair actually qualified for it? Does their body of work justify tenure? Or are they there by patronage whilst blocking others and extorting those beneath them?*

The era of blind reverence is over. The **Students Liberation Engine** exists to restore academic merit, expose the comprador class in academia, end impunity, and fight for a people's education free from extortion, gender oppression and patronage.

*For every student bounced between offices at KeMU, UoN, KU, Moi, Egerton, JKUAT, Maseno, TUK, KPU, and every polytechnic fighting for their rightful marks. Solidarity with those currently protesting corrupt educators. The masses have nothing to lose but their chains.*
