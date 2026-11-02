# SexForGrades

**Exposing Academic Extortion & Missing Marks Corruption in Kenyan Universities and Polytechnics**

A zero-dependency, auditable ledger of evidence for a system where grades are bartered, missing marks are weaponized, and accountability is buried under bureaucracy. Built to document, compare, and preserve testimonies of extortion across Kenya's institutions of higher learning.

## The Kenyan Reality

Across Kenyan universities and polytechnics, a deeply entrenched culture of **sex-for-grades** and **extortion-for-marks** has persisted for decades. Lecturers and some corrupt faculty members deliberately delay, withhold, or "misplace" examination marks to coerce students into sexual favors, bribes, or other illicit concessions. 

This is not isolated misconduct. It is systemic. When students dare to protest, ask for clarification, or demand their legitimately earned marks, they are met with intimidation, victimization, endless "marking in progress" excuses, and in many cases, the very people facilitating corruption are the ones loudly protesting reform whilst protecting each other.

## A Personal Account: Kenya Methodist University (KeMU)

The author of this project knows this reality firsthand. At **Kenya Methodist University (KeMU)**, a university founded and heavily influenced by the **GEMA** network of communities, the author experienced the weaponization of missing marks firsthand. What should have been a straightforward academic process turned into a labyrinth of obstruction, selective delays, and runarounds designed to frustrate and pressure. 

KeMU markets itself as a Christian university, yet behind its pulpit of morality lies a deeply troubling culture of silencing. There is a persistent pattern of prioritizing **theology, business and "acceptable" courses** while systematically undermining and frustrating students in the **pure sciences**. The sciences - mathematics, biology, chemistry, physics and related technical fields - are treated as inconvenient. Students pursuing them are disproportionately subjected to missing marks, inexplicable failures, delayed results, and bureaucratic gaslighting, all while the institution claims Christian values.

## What This Tool Does

`SexForGrades` is a forensic comparison tool adapted from robust winnowing algorithms. Originally built for plagiarism detection, its utility here is inverted: **preserve evidence, detect duplication of cover-ups, and maintain an immutable, auditable corpus of testimonies.**

- **Evidence Preservation** - Store testimonies, emails, petition letters, senate complaints, and documented correspondences in a local, zero-dependency corpus.
- **Pattern Detection** - Compare documents to identify repeated boilerplate responses from departments (the "your marks are with the lecturer" script used across faculties and years).
- **Forensic Inspection** - Identify zero-width characters, tampered documents, or suspicious edits using built-in forensics.
- **Local & Private** - Everything stays on your machine. No data sent to third parties. Fully auditable Python standard library only.
- **HTML Reports** - Generate clear, shareable reports for petitions, student unions, media, or legal advocacy.

## Quick Start

Requires Python 3.11+. No external dependencies.

```bash
# Build a corpus of evidence
python3 -m sexforgrades index corpus --out evidence.index.json

# Compare testimonies to detect shared cover-up patterns
python3 -m sexforgrades check testimony.txt --index evidence.index.json --html report.html

# Inspect a suspicious document for tampering
python3 -m sexforgrades inspect email_from_office.eml --json

# Find internal repetition in a long petition
python3 -m sexforgrades internal petition.txt
```

## The Fight

This project exists in solidarity with every Kenyan student who has been told "come next semester", every student who has been asked for "something small" to clear a missing mark, every science student at KeMU who has watched less-qualified peers pass whilst they are bounced between offices, and every brave student currently protesting against corrupt educators protecting their impunity.

**Missing marks are not administrative errors. In too many cases, they are deliberate weapons of extortion.**

*Silence protects the perpetrators. Documentation protects the victims.*

## License

This project is released for the purpose of documentation, evidence preservation and advocacy. Use it to document the truth.
