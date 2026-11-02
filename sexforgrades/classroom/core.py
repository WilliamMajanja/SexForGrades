"""Classroom core - self-paced, mastery-based, offline-first."""
from __future__ import annotations

import json
from pathlib import Path


class PeoplesClassroom:
    def __init__(self, library_root="./classroom_library"):
        self.library_root = Path(library_root)
        self.library_root.mkdir(parents=True, exist_ok=True)
        (self.library_root / "public_domain" / "cs").mkdir(parents=True, exist_ok=True)

    def catalog(self):
        items = []
        for p in self.library_root.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".pdf", ".txt", ".md", ".epub", ".html"):
                items.append({"path": str(p), "name": p.name, "category": p.parent.name})
        return {"count": len(items), "items": items}

    def add_public_domain_book(self, title, author, path, metadata=None):
        meta = {"title": title, "author": author, "public_domain": True, "source": "public_domain", **(metadata or {})}
        out = self.library_root / "public_domain" / "cs" / f"{title.replace(' ', '_')}.meta.json"
        out.write_text(json.dumps(meta, indent=2))
        return meta
