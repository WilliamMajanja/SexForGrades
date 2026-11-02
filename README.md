# SexForGrades — Students Liberation Engine (SLE)

**A Students Liberation Engine built to question, audit and expose the legitimacy of tenured professorships across Kenya's public universities, private universities, and national polytechnics.**

A zero-dependency, fully auditable forensic toolkit for students to verify academic credentials, publication records, supervision claims, and the integrity of those entrusted with power over their futures.

## The Kenyan Crisis

For decades, Kenya's higher education sector has been captured by a culture of impunity. Positions of power — especially **tenured professorships, associate professorships, and senior academic posts** — have increasingly gone to individuals whose credentials, research output, and academic lineage do not withstand scrutiny. 

Lecturers and some professors weaponize **missing marks, delayed results, arbitrary failures, and sexual/coercive extortion (sex-for-grades)** to subjugate students whilst hiding behind titles they may not have legitimately earned. Those who dare to question are gaslit with "respect your professor", threatened, or victimized through the very systems they control.

## Kenya Methodist University (KeMU) — A Case Study

The author's firsthand experience at **Kenya Methodist University (KeMU)** is instructive. KeMU presents itself as a Christian university, yet operates under the influence of the **GEMA** patronage network. In practice, this has translated to:
- **Suppression of the sciences** — Students pursuing pure sciences (Mathematics, Physics, Chemistry, Biology, Computer Science, and related technical fields) are disproportionately subjected to missing marks, inexplicable grade changes, delayed processing, and administrative obstruction.
- **Protection of the connected** — Those with political, ethnic, or institutional connections are shielded regardless of competence or conduct.
- **Weaponized bureaucracy** — Complaints about missing marks vanish into committees whilst students suffer lost graduation dates, missed scholarships, and blocked opportunities.
- **Credential opacity** — Many students have no way to verify if the people grading them or holding senior titles actually possess the qualifications they claim.

## The Students Liberation Engine

SexForGrades is reimagined as the **Students Liberation Engine (SLE)**. It is a tool for academic accountability — empowering students to systematically audit those in power using publicly verifiable information.

### Core Capabilities

- **Professor Qualification Audit** - Compare CVs, profiles, and published claims against verifiable records. Build a corpus of evidence on individuals holding tenured/senior posts.
- **Publication Forensics** - Detect duplicate or recycled publications, suspiciously identical abstracts, and boilerplate text across "research" output.
- **Thesis Supervision Mapping** - Document and cross-reference who claims to supervise in fields they have no demonstrable expertise in.
- **Missing Marks Ledger** - Maintain an immutable, student-driven record of missing marks, extortion attempts, and cover-up patterns across departments.
- **Document Pattern Detection** - Using robust winnowing (MOSS-style) fingerprinting, detect identical "committee response" letters sent to multiple students over years of complaints.
- **Forensic Inspection** - Detect tampering: zero-width characters, bidirectional text, suspicious edits, and document anomalies.
- **Zero-Dependency & Auditable** - Entirely Python standard library. Runs locally. No cloud uploads. Every line of code is readable and verifiable.

## Quick Start

```bash
# Build an evidence corpus of professor profiles, CVs, responses, and testimonies
python3 -m sexforgrades index corpus --out sle.index.json

# Compare a suspect CV/publication against known records
python3 -m sexforgrades check professor_cv.txt --index sle.index.json --html audit_report.html

# Detect repeated cover-up responses across complaints
python3 -m sexforgrades internal committee_response.txt

# Forensically inspect a suspicious document/email
python3 -m sexforgrades inspect suspicious_letter.pdf --json
```

## Guiding Principles

- **Students First** - The engine belongs to students. It is a weapon of documentation, not defamation. Stick to verifiable facts, documents, and public records.
- **Evidence Over Hearsay** - Prioritize public profiles, official documents, emails, published papers, and firsthand documented testimony.
- **Expose, Don't Harass** - The goal is institutional accountability and reform, not personal vendettas.
- **Transparency** - The code must remain open, auditable, and free from hidden data exfiltration.
- **Liberation Through Knowledge** - Informed students cannot be gaslit as easily. An educated student body armed with facts is the greatest threat to academic impunity.

## The Mission

**Question everything. Document everything. Verify everything.**

Every student deserves to know: *Is the person holding a professorial chair actually qualified for it? Does their body of work justify tenure? Or are they there by patronage whilst blocking others and extorting those beneath them?*

The era of blind reverence is over. The Students Liberation Engine exists to restore academic merit, protect the sciences, and end the impunity that has rotted Kenyan higher education from within.

*For every student bounced between offices at KeMU, UoN, KU, Moi, Egerton, JKUAT, Maseno, TUK, KPU, and every polytechnic fighting for their rightful marks.*
