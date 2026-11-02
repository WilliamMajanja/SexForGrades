"""Text normalization.

Tokenization keeps every token's character span in the original string so that
matches can be highlighted in place. Optional filters (quotes, references) blank
a region in place -- replacing characters with spaces rather than deleting them
-- so character offsets stay valid for the whole pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A word is one or more letters/digits, optionally joined by internal apostrophes
# (straight or curly), e.g. "don't", "O'Brien", "Ngũgĩ".
TOKEN_RE = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*", re.UNICODE)

# Quote spans: straight double quotes and curly double quotes.
QUOTE_RE = re.compile(r'"[^"]*"|\u201c[^\u201d]*\u201d', re.DOTALL)

REFERENCES_HEADING_RE = re.compile(
    r"(?im)^[ \t]*(?:references|bibliography|works[ \t]+cited|"
    r"literature[ \t]+cited|references[ \t]+cited)[ \t]*:?[ \t]*$"
)


@dataclass(frozen=True)
class Token:
    """A single normalized token with its span in the source string."""

    text: str
    start: int
    end: int
    normal: str

    def __len__(self) -> int:  # convenience: token count is always one
        return 1


def tokenize(text: str) -> list[Token]:
    """Return the list of tokens in *text* with original character offsets."""

    tokens: list[Token] = []
    for match in TOKEN_RE.finditer(text):
        raw = match.group(0)
        tokens.append(Token(raw, match.start(), match.end(), raw.casefold()))
    return tokens


def _blank(masked: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if masked[index] not in "\r\n":
            masked[index] = " "


def mask_quotes(text: str) -> str:
    """Return *text* with quoted spans blanked out, preserving length.

    Only characters inside quotation marks are replaced; line breaks survive so
    paragraph structure is unchanged. Used to approximate Turnitin's
    "exclude quotes" behaviour.
    """

    masked = list(text)
    for match in QUOTE_RE.finditer(text):
        _blank(masked, match.start(), match.end())
    return "".join(masked)


def mask_references(text: str) -> str:
    """Return *text* with the final references/bibliography list blanked out.

    The reference list is assumed to start at the last line that is exactly a
    heading such as "References", "Bibliography" or "Works Cited". Everything
    from that line to the end is blanked, preserving length.
    """

    matches = list(REFERENCES_HEADING_RE.finditer(text))
    if not matches:
        return text
    masked = list(text)
    _blank(masked, matches[-1].start(), len(text))
    return "".join(masked)


def apply_filters(
    text: str, *, exclude_quotes: bool = False, exclude_references: bool = False
) -> str:
    """Apply the requested in-place filters and return the masked text."""

    result = text
    if exclude_quotes:
        result = mask_quotes(result)
    if exclude_references:
        result = mask_references(result)
    return result
