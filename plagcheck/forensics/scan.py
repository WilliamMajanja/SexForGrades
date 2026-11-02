from __future__ import annotations

import re
import unicodedata


ZWSP = [
    "\u200b",  # zero width space
    "\u200c",  # zwnj
    "\u200d",  # zwj
    "\u2060",  # word joiner
    "\ufeff",  # bom/zwnbsp
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
]


def scan_text(text: str):
    findings = []
    # zero width
    counts = {}
    for z in ZWSP:
        c = text.count(z)
        if c:
            counts[z] = c
    if counts:
        total = sum(counts.values())
        findings.append(
            {
                "kind": "forensics/zwsp",
                "detail": f"{total} zero-width/bidi control chars",
                "evidence": counts,
            }
        )
    # soft hyphen
    sh = text.count("\u00ad")
    if sh:
        findings.append({"kind": "forensics/soft_hyphen", "detail": f"{sh} soft hyphens"})
    # mixed whitespace
    if "\t" in text and "\n" in text:
        # not an error, just note
        pass
    # unusual spaces
    nbsp = text.count("\u00a0")
    if nbsp:
        findings.append({"kind": "forensics/nbsp", "detail": f"{nbsp} non-breaking spaces"})
    # bidirectional
    bidi_marks = ["\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069"]
    bc = sum(text.count(x) for x in bidi_marks)
    if bc:
        findings.append({"kind": "forensics/bidi", "detail": f"{bc} bidirectional marks"})
    # homoglyph-like (very rough) - check for cyrillic in mostly latin words
    # just flag if mixed scripts heavily
    try:
        scripts = set()
        for ch in text:
            if ch.isalpha():
                try:
                    scripts.add(unicodedata.name(ch).split()[0])
                except Exception:
                    pass
        if "CYRILLIC" in scripts and "LATIN" in scripts:
            findings.append(
                {"kind": "forensics/mixed_script", "detail": "mixed Latin/Cyrillic scripts detected"}
            )
    except Exception:
        pass
    return findings


scan = scan_text
