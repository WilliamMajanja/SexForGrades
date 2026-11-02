"""Word n-gram fingerprinting with the winnowing selection algorithm.

Pipeline:

1. Each token is reduced to a stable 64-bit hash (BLAKE2b).
2. A rolling polynomial hash turns the token hashes into overlapping k-gram
   hashes (one per starting position).
3. Winnowing keeps, for every window of *w* consecutive k-grams, the minimum
   hash. This reduces storage while guaranteeing that any shared passage of at
   least k + w - 1 tokens contributes at least one shared fingerprint.

This is the MOSS-style guarantee used to make matching robust to local edits.
"""

from __future__ import annotations

import hashlib
from collections import deque

from .normalize import Token

MASK = (1 << 64) - 1
BASE = 0x100000001B3  # FNV-1a 64-bit prime

DEFAULT_K = 5
DEFAULT_W = 4


def token_hashes(tokens: list[Token]) -> list[int]:
    """Return a stable 64-bit hash for each token's normalized form."""

    return [
        int.from_bytes(
            hashlib.blake2b(token.normal.encode("utf-8"), digest_size=8).digest(),
            "big",
        )
        for token in tokens
    ]


def shingle_hashes(hashes: list[int], k: int) -> list[int]:
    """Return rolling polynomial hashes for all overlapping k-grams.

    ``result[i]`` is the hash of ``hashes[i:i + k]``; the list has
    ``max(0, len(hashes) - k + 1)`` entries.
    """

    if k <= 0:
        raise ValueError("shingle size k must be positive")
    n = len(hashes)
    if n < k:
        return []
    modulus = 1 << 64
    power = pow(BASE, k - 1, modulus)
    window = 0
    for index in range(k):
        window = (window * BASE + hashes[index]) & MASK
    out = [0] * (n - k + 1)
    out[0] = window
    for index in range(1, n - k + 1):
        window = ((window - hashes[index - 1] * power) * BASE + hashes[index + k - 1]) & MASK
        out[index] = window
    return out


def winnow(shingles: list[int], w: int) -> list[tuple[int, int]]:
    """Select fingerprints using a sliding window of width *w*.

    Returns a list of ``(start_index, hash)`` pairs, in increasing start order,
    with no duplicate positions. On ties the rightmost minimum is chosen.
    """

    if w <= 0:
        raise ValueError("window size w must be positive")
    n = len(shingles)
    if n == 0:
        return []
    if n < w:
        best = min(shingles)
        return [(shingles.index(best), best)]

    selected: list[tuple[int, int]] = []
    candidates: deque[int] = deque()
    last_selected = -1
    for index in range(n):
        while candidates and shingles[candidates[-1]] >= shingles[index]:
            candidates.pop()
        candidates.append(index)
        if candidates[0] <= index - w:
            candidates.popleft()
        if index >= w - 1:
            minimum = candidates[0]
            if minimum != last_selected:
                selected.append((minimum, shingles[minimum]))
                last_selected = minimum
    return selected


def fingerprint_tokens(
    tokens: list[Token], k: int = DEFAULT_K, w: int = DEFAULT_W
) -> list[tuple[int, int]]:
    """Convenience wrapper: tokenize -> hash -> k-gram -> winnow."""

    return winnow(shingle_hashes(token_hashes(tokens), k), w)


def guarantee_length(k: int, w: int) -> int:
    """Minimum match length (in tokens) guaranteed by the fingerprint set."""

    return k + w - 1
