"""SexForGrades: documenting missing marks corruption in Kenyan Universities and Polytechnics., Turnitin-style text similarity checker.

The package uses only the Python standard library. It fingerprints text with
word n-grams and the winnowing algorithm (Schleimer, Wilkerson and Aiken, 2003)
and reports which passages of a submitted document match a local corpus and,
optionally, user-supplied web sources.
"""

from __future__ import annotations

__version__ = "1.0.0"

from .normalize import Token, tokenize, mask_quotes, mask_references
from .fingerprint import (
    fingerprint_tokens,
    shingle_hashes,
    token_hashes,
    winnow,
)
from .index import CorpusIndex, Document
from .compare import (
    MatchRun,
    Result,
    SourceHit,
    analyze,
    analyze_internal,
)
from .extract import extract_text, SUPPORTED_SUFFIXES

__all__ = [
    "__version__",
    "Token",
    "tokenize",
    "mask_quotes",
    "mask_references",
    "fingerprint_tokens",
    "shingle_hashes",
    "token_hashes",
    "winnow",
    "CorpusIndex",
    "Document",
    "MatchRun",
    "Result",
    "SourceHit",
    "analyze",
    "analyze_internal",
    "extract_text",
    "SUPPORTED_SUFFIXES",
]
