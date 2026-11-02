"""Inspector registry, envelopes and shared helpers."""

import hashlib
import os
from pathlib import Path

SCHEMA = "plagcheck.v1"

_READ_SIZE = 65536

REGISTRY = []


class Inspection:
    """Mutable envelope dict wrapper with helper builders."""

    def __init__(self, fmt, confidence=1.0):
        self.format = fmt
        self.confidence = confidence
        self.summary = ""
        self.findings = []
        self.limits = []

    def add_finding(self, kind, detail, evidence=None, **extra):
        f = {"kind": kind, "detail": detail}
        if evidence is not None:
            f["evidence"] = evidence
        if extra:
            f.update(extra)
        self.findings.append(f)
        return f

    def add_limit(self, text):
        self.limits.append(text)

    def envelope(self, path):
        return {
            "schema": SCHEMA,
            "file": file_facts(path),
            "format": self.format,
            "confidence": round(self.confidence, 3),
            "summary": self.summary,
            "findings": self.findings,
            "limits": self.limits,
        }


def file_facts(path):
    facts = {"path": str(Path(path).resolve())}
    try:
        facts["size"] = os.path.getsize(path)
    except Exception:
        facts["size"] = 0
    try:
        import stat

        st = os.stat(path)
        facts["mode"] = stat.filemode(st.st_mode)
    except Exception:
        pass
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        facts["sha256"] = h.hexdigest()
    except Exception:
        pass
    return facts


def err_envelope(path, message):
    return {
        "schema": SCHEMA,
        "file": {"path": str(Path(path).resolve())},
        "error": message,
    }


class Format:
    """A file format inspector."""

    name = ""
    description = ""
    confidence = 1.0
    deps = "stdlib-only"
    extensions = []

    def match(self, buf, size):  # pragma: no cover - overridden
        return 0.0

    def inspect(self, path, buf, size):  # pragma: no cover - overridden
        raise NotImplementedError


def register(fmt_cls):
    if fmt_cls not in REGISTRY:
        REGISTRY.append(fmt_cls)
    return fmt_cls


def identify(path):
    """Return the best-matching (Format, confidence, buf, size)."""
    apath = Path(path)
    if not apath.is_file():
        raise FileNotFoundError(f"no such file: {apath}")
    with open(apath, "rb") as fh:
        buf = memoryview(fh.read(_READ_SIZE))
    size = os.path.getsize(apath)
    best, score = None, 0.0
    for cls in REGISTRY:
        fmt = cls()
        try:
            s = float(fmt.match(buf, size))
        except Exception:
            s = 0.0
        if s > score:
            best, score = fmt, s
    return best, score, buf, size


def inspect_file(path, fmt_name=None):
    """Inspect a file; results include evidence and limitations."""
    apath = Path(path)
    best, score, buf, size = identify(apath)
    chosen = best
    if fmt_name is not None:
        fmt_name = fmt_name.lower()
        for cls in REGISTRY:
            f = cls()
            if f.name == fmt_name:
                chosen = f
                break
        else:
            raise ValueError(f"unknown format: {fmt_name}")

    if chosen is None:
        return err_envelope(apath, "no matching format")

    try:
        ins = chosen.inspect(apath, bytes(buf), size)
    except Exception as e:
        return err_envelope(apath, str(e))

    if isinstance(ins, Inspection):
        env = ins.envelope(apath)
    elif isinstance(ins, dict):
        env = ins
        if "schema" not in env:
            env["schema"] = SCHEMA
        if "file" not in env or not isinstance(env.get("file"), dict):
            env["file"] = file_facts(apath)
    else:
        return err_envelope(apath, "invalid inspection result")

    env["format"] = getattr(chosen, "name", env.get("format"))
    env["confidence"] = round(float(env.get("confidence", score)), 3)
    return env


def list_formats():
    out = []
    for cls in REGISTRY:
        f = cls()
        out.append(
            {
                "format": f.name,
                "description": f.description,
                "extensions": list(getattr(f, "extensions", [])),
                "deps": getattr(f, "deps", "stdlib-only"),
            }
        )
    return out
