"""Comparison engine: match a submitted document against a corpus index."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .fingerprint import guarantee_length, shingle_hashes, token_hashes
from .index import CorpusIndex
from .normalize import Token, apply_filters, tokenize


@dataclass
class MatchRun:
    """A maximal region of the submission matched against one or more sources."""

    token_start: int
    token_end: int  # exclusive
    char_start: int
    char_end: int
    sources: list[str]
    text: str

    @property
    def words(self) -> int:
        return self.token_end - self.token_start

    def to_dict(self) -> dict:
        return {
            "token_start": self.token_start,
            "token_end": self.token_end,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "sources": self.sources,
            "words": self.words,
            "text": self.text,
        }


@dataclass
class SourceHit:
    """Per-source breakdown of matched text."""

    source_id: str
    title: str
    matched_words: int
    percent: float
    matches: list[MatchRun] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "matched_words": self.matched_words,
            "percent": round(self.percent, 2),
            "match_count": len(self.matches),
            "matches": [match.to_dict() for match in self.matches],
        }


@dataclass
class Result:
    """Full analysis result for one submission."""

    total_words: int
    matched_words: int
    percent: float
    sources: list[SourceHit]
    runs: list[MatchRun]
    analyzed_text: str
    excluded_words: int = 0
    k: int = 5
    w: int = 4
    guarantee: int = 8

    @property
    def score_band(self) -> str:
        """Coarse Turnitin-style band label for the overall percentage."""

        score = self.percent
        if score <= 10:
            return "low"
        if score <= 25:
            return "moderate"
        if score <= 50:
            return "high"
        return "very high"

    def to_dict(self) -> dict:
        return {
            "total_words": self.total_words,
            "matched_words": self.matched_words,
            "percent": round(self.percent, 2),
            "score_band": self.score_band,
            "excluded_words": self.excluded_words,
            "parameters": {"k": self.k, "w": self.w, "guarantee": self.guarantee},
            "source_count": len(self.sources),
            "sources": [source.to_dict() for source in self.sources],
            "matches": [run.to_dict() for run in self.runs],
        }


def _marked_regions(
    tokens: list[Token],
    shingles: list[int],
    postings: dict[int, dict[str, int]],
    k: int,
) -> tuple[list[bool], list[dict[str, int] | None]]:
    marked = [False] * len(tokens)
    per_shingle: list[dict[str, int] | None] = [None] * len(shingles)
    for index, value in enumerate(shingles):
        entry = postings.get(value)
        if entry:
            per_shingle[index] = entry
            end = min(index + k, len(marked))
            for position in range(index, end):
                marked[position] = True
    return marked, per_shingle


def _runs_from_marks(
    tokens: list[Token],
    text: str,
    marked: list[bool],
    per_shingle: list[dict[str, int] | None],
    k: int,
    min_run: int,
) -> list[MatchRun]:
    runs: list[MatchRun] = []
    total = len(tokens)
    index = 0
    while index < total:
        if not marked[index]:
            index += 1
            continue
        end = index
        while end < total and marked[end]:
            end += 1
        if end - index >= min_run:
            sources: set[str] = set()
            for shingle_start in range(max(0, index - k + 1), min(end, len(per_shingle))):
                entry = per_shingle[shingle_start]
                if entry:
                    sources.update(entry.keys())
            run = MatchRun(
                token_start=index,
                token_end=end,
                char_start=tokens[index].start,
                char_end=tokens[end - 1].end,
                sources=sorted(sources),
                text=text[tokens[index].start : tokens[end - 1].end],
            )
            runs.append(run)
        index = end
    return runs


def analyze(
    text: str,
    index: CorpusIndex,
    *,
    min_run: int | None = None,
    exclude_quotes: bool = False,
    exclude_references: bool = False,
) -> Result:
    """Compare *text* against *index* and return a :class:`Result`."""

    filtered = apply_filters(
        text,
        exclude_quotes=exclude_quotes,
        exclude_references=exclude_references,
    )
    tokens = tokenize(filtered)
    total_words = len(tokens)
    excluded_words = len(tokenize(text)) - total_words
    threshold = guarantee_length(index.k, index.w) if min_run is None else min_run
    if threshold > total_words:
        return Result(
            total_words=total_words,
            matched_words=0,
            percent=0.0,
            sources=[],
            runs=[],
            analyzed_text=text,
            excluded_words=excluded_words,
            k=index.k,
            w=index.w,
            guarantee=guarantee_length(index.k, index.w),
        )

    hashes = token_hashes(tokens)
    shingles = shingle_hashes(hashes, index.k)
    marked, per_shingle = _marked_regions(tokens, shingles, index.postings, index.k)
    runs = _runs_from_marks(
        tokens, filtered, marked, per_shingle, index.k, threshold
    )

    matched_words = sum(run.words for run in runs)
    per_source_words: dict[str, int] = defaultdict(int)
    per_source_runs: dict[str, list[MatchRun]] = defaultdict(list)
    for run in runs:
        for source_id in run.sources:
            per_source_words[source_id] += run.words
            per_source_runs[source_id].append(run)

    sources = [
        SourceHit(
            source_id=source_id,
            title=index.title_for(source_id),
            matched_words=words,
            percent=(words / total_words * 100.0) if total_words else 0.0,
            matches=per_source_runs[source_id],
        )
        for source_id, words in per_source_words.items()
    ]
    sources.sort(key=lambda hit: (-hit.matched_words, hit.source_id))

    percent = (matched_words / total_words * 100.0) if total_words else 0.0
    return Result(
        total_words=total_words,
        matched_words=matched_words,
        percent=percent,
        sources=sources,
        runs=sorted(runs, key=lambda run: run.char_start),
        analyzed_text=text,
        excluded_words=excluded_words,
        k=index.k,
        w=index.w,
        guarantee=guarantee_length(index.k, index.w),
    )


@dataclass
class InternalDuplicate:
    """A phrase repeated within a single document."""

    phrase: str
    first_char: int
    second_char: int
    words: int

    def to_dict(self) -> dict:
        return {
            "phrase": self.phrase,
            "first_char": self.first_char,
            "second_char": self.second_char,
            "words": self.words,
        }


def analyze_internal(
    text: str, *, k: int = 8, min_occurrences: int = 2
) -> dict:
    """Detect repeated phrases within one document (self-plagiarism).

    Returns a dict with the total word count, duplicated word count, a
    percentage and the duplicate examples. Uses exact k-gram matching.
    """

    tokens = tokenize(text)
    if k <= 0:
        raise ValueError("k must be positive")
    if len(tokens) < k:
        return {
            "total_words": len(tokens),
            "duplicated_words": 0,
            "percent": 0.0,
            "duplicates": [],
        }

    hashes = token_hashes(tokens)
    shingles = shingle_hashes(hashes, k)
    positions: dict[int, list[int]] = defaultdict(list)
    for index, value in enumerate(shingles):
        positions[value].append(index)

    repeated = {
        value: starts
        for value, starts in positions.items()
        if len(starts) >= min_occurrences
    }
    marked = [False] * len(tokens)
    examples: list[InternalDuplicate] = []
    seen_phrases: set[str] = set()
    for value, starts in repeated.items():
        for start in starts:
            for position in range(start, start + k):
                marked[position] = True
        first, second = starts[0], starts[1]
        phrase = text[tokens[first].start : tokens[first + k - 1].end]
        key = phrase.casefold()
        if key not in seen_phrases:
            seen_phrases.add(key)
            examples.append(
                InternalDuplicate(
                    phrase=phrase,
                    first_char=tokens[first].start,
                    second_char=tokens[second].start,
                    words=k,
                )
            )
    duplicated_words = sum(marked)
    examples.sort(key=lambda item: item.phrase.casefold())
    return {
        "total_words": len(tokens),
        "duplicated_words": duplicated_words,
        "percent": (duplicated_words / len(tokens) * 100.0) if tokens else 0.0,
        "duplicates": [example.to_dict() for example in examples[:200]],
        "k": k,
    }
