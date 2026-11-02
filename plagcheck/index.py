"""Corpus index: an inverted map from fingerprint to source documents."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .fingerprint import DEFAULT_K, DEFAULT_W, fingerprint_tokens
from .normalize import apply_filters, tokenize


@dataclass
class Document:
    """A single reference document held in the corpus."""

    doc_id: str
    title: str
    path: str = ""
    word_count: int = 0
    fingerprints: int = 0

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "path": self.path,
            "word_count": self.word_count,
            "fingerprints": self.fingerprints,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        return cls(
            doc_id=data["doc_id"],
            title=data.get("title", data["doc_id"]),
            path=data.get("path", ""),
            word_count=int(data.get("word_count", 0)),
            fingerprints=int(data.get("fingerprints", 0)),
        )


@dataclass
class CorpusIndex:
    """Fingerprint index over a set of reference documents.

    ``postings`` maps a fingerprint to ``{doc_id: first_token_start}`` so a match
    can be attributed to sources and, where useful, located within a source.
    """

    k: int = DEFAULT_K
    w: int = DEFAULT_W
    documents: list[Document] = field(default_factory=list)
    postings: dict[int, dict[str, int]] = field(default_factory=dict)
    _doc_ids: set[str] = field(default_factory=set, repr=False)

    @property
    def guarantee(self) -> int:
        from .fingerprint import guarantee_length

        return guarantee_length(self.k, self.w)

    def add_document(
        self,
        doc_id: str,
        title: str,
        text: str,
        *,
        path: str = "",
        exclude_quotes: bool = False,
        exclude_references: bool = False,
    ) -> Document:
        """Fingerprint *text* and add it to the index."""

        if doc_id in self._doc_ids:
            raise ValueError(f"duplicate document id: {doc_id}")
        filtered = apply_filters(
            text,
            exclude_quotes=exclude_quotes,
            exclude_references=exclude_references,
        )
        tokens = tokenize(filtered)
        prints = fingerprint_tokens(tokens, self.k, self.w)
        for start, value in prints:
            self.postings.setdefault(value, {})[doc_id] = start
        document = Document(
            doc_id=doc_id,
            title=title,
            path=path,
            word_count=len(tokens),
            fingerprints=len(prints),
        )
        self.documents.append(document)
        self._doc_ids.add(doc_id)
        return document

    def source_count(self) -> int:
        return len(self.documents)

    def to_dict(self) -> dict:
        return {
            "k": self.k,
            "w": self.w,
            "documents": [document.to_dict() for document in self.documents],
            "postings": [
                [int(value), list(entry.items())]
                for value, entry in self.postings.items()
            ],
        }

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        destination.write_text(
            json.dumps(self.to_dict(), separators=(",", ":")), encoding="utf-8"
        )

    @classmethod
    def from_dict(cls, data: dict) -> "CorpusIndex":
        index = cls(k=int(data.get("k", DEFAULT_K)), w=int(data.get("w", DEFAULT_W)))
        for entry in data.get("documents", []):
            document = Document.from_dict(entry)
            index.documents.append(document)
            index._doc_ids.add(document.doc_id)
        for value, pairs in data.get("postings", []):
            index.postings[int(value)] = {doc_id: int(start) for doc_id, start in pairs}
        return index

    @classmethod
    def load(cls, path: str | Path) -> "CorpusIndex":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def title_for(self, doc_id: str) -> str:
        for document in self.documents:
            if document.doc_id == doc_id:
                return document.title
        return doc_id


def build_index(
    documents: Iterable[tuple[str, str, str]],
    *,
    k: int = DEFAULT_K,
    w: int = DEFAULT_W,
    exclude_quotes: bool = False,
    exclude_references: bool = False,
) -> CorpusIndex:
    """Build an index from ``(doc_id, title, text)`` triples."""

    index = CorpusIndex(k=k, w=w)
    for doc_id, title, text in documents:
        index.add_document(
            doc_id,
            title,
            text,
            exclude_quotes=exclude_quotes,
            exclude_references=exclude_references,
        )
    return index
