"""Command-line interface for plagcheck."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from . import extract
from . import index as indexmod
from . import compare
from . import report
from . import webapp

try:
    from . import formats  # noqa
except Exception:
    pass
from .core import registry


BANNER = r"""
    ╔═╗╦  ╔═╗╔═╗╔═╗╦ ╦╔═╗╔═╗╦╔═╗
    ║╣ ║  ╠═╣║ ╦║  ╠═╣╠═╣║  ╠╩╗
    ╚═╝╩═╝╩ ╩╚═╝╚═╝╩ ╩╩ ╩╚═╝╩ ╚═╝
        turnitout-grade • zero-dep • v{v}
"""


def _print(o):
    json.dump(o, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def cmd_identify(args):
    try:
        registry.identify(args.path)
        facts = registry.inspect_file(args.path)
    except Exception as e:
        print(f"plagcheck: {e}", file=sys.stderr)
        return 1
    ins = {
        "schema": facts.get("schema"),
        "format": facts.get("format"),
        "confidence": facts.get("confidence"),
        "summary": facts.get("summary", ""),
        "file": facts.get("file"),
    }
    if args.json:
        _print(ins)
    else:
        if not args.quiet:
            print(BANNER.replace("{v}", __version__))
        print(f"format      : {ins['format']}")
        print(f"confidence  : {ins['confidence']}")
        print(f"summary     : {ins['summary']}")
        if ins.get("file"):
            print(f"size        : {ins['file'].get('size')} bytes")
            print(f"sha256      : {ins['file'].get('sha256')}")
    return 0


def cmd_inspect(args):
    try:
        envelope = registry.inspect_file(args.path, fmt_name=args.format)
    except Exception as e:
        print(f"plagcheck: {e}", file=sys.stderr)
        return 2
    if args.json:
        _print(envelope)
    else:
        if not args.quiet:
            print(BANNER.replace("{v}", __version__))
        print("-" * 60)
        print(f"format : {envelope.get('format')}  (confidence {envelope.get('confidence')})")
        print(f"summary: {envelope.get('summary')}")
        f = envelope.get("file") or {}
        if isinstance(f, dict):
            print(f"file   : {f.get('path')} ({f.get('size')} bytes)")
            print(f"sha256 : {f.get('sha256','n/a')}")
        print("-" * 60)
        for finding in envelope.get("findings", []):
            ev = finding.get("evidence")
            line = f"  [{finding['kind']:>18}] {finding['detail']}"
            if ev is not None and not args.compact:
                try:
                    evs = json.dumps(ev)
                except Exception:
                    evs = str(ev)
                line += f"  | evidence: {evs}"
            print(line)
        for lim in envelope.get("limits", []):
            print(f"  limit                : {lim}")
        if envelope.get("error"):
            print(f"  error                : {envelope['error']}")
        print("-" * 60)
    return 0


def cmd_list_formats(args):
    fmts = registry.list_formats()
    if args.json:
        _print(fmts)
        return 0
    if not args.quiet:
        print(BANNER.replace("{v}", __version__))
    width = max(len(f["format"]) for f in fmts) + 2
    for f in fmts:
        exts = ",".join(f.get("extensions") or [])
        print(f"  {f['format']:<{width}} {f['description']}  [{exts}]")
    print(f"\n  {len(fmts)} format(s), stdlib-only.")
    return 0


def _load_corpus(corpus_dir=None, index_path=None):
    if index_path:
        return indexmod.CorpusIndex.load(index_path)
    ci = indexmod.CorpusIndex()
    if corpus_dir:
        ci.build(corpus_dir)
    return ci


def cmd_index(args):
    ci = indexmod.CorpusIndex()
    ci.build(args.corpus)
    ci.save(args.out)
    print(f"Indexed {len(ci.documents)} documents -> {args.out}")
    return 0


def cmd_check(args):
    ci = _load_corpus(args.corpus, args.index)
    if args.submission_text:
        submission_text = args.submission_text
    elif args.file:
        submission_text = extract.extract_text(args.file)
    else:
        submission_text = sys.stdin.read()

    res = compare.analyze(
        submission_text,
        ci,
        k=args.k,
        w=args.w,
        min_run=args.min_run,
        exclude_quotes=args.exclude_quotes,
        exclude_references=args.exclude_references,
        urls=args.url or [],
    )
    if getattr(args, "json_report", False):
        _print(res.to_dict())
        return 0
    if getattr(args, "text_report", False) or (not getattr(args, "html", None) and not getattr(args, "json_out", None)):
        print(report.text_report(res))
    if getattr(args, "html", None):
        report.write_html(res, args.html)
        print(f"Wrote HTML report to {args.html}")
    if getattr(args, "json_out", None):
        report.write_json(res, args.json_out)
        print(f"Wrote JSON report to {args.json_out}")
    return 0


def cmd_internal(args):
    if args.file:
        submission_text = extract.extract_text(args.file)
    elif getattr(args, "submission_text", None):
        submission_text = args.submission_text
    else:
        submission_text = sys.stdin.read()
    res = compare.analyze_internal(submission_text, k=args.k, w=args.w, min_run=args.min_run)
    if args.json:
        _print(res.to_dict())
        return 0
    print(report.text_report(res))
    return 0


def cmd_serve(args):
    webapp.serve(port=args.port, corpus_dir=args.corpus, index_path=args.index)
    return 0


def cmd_gui(args):
    try:
        from . import gui

        gui.run(corpus_dir=args.corpus, index_path=args.index)
    except Exception as e:
        print(f"plagcheck: gui unavailable: {e}", file=sys.stderr)
        print("Hint: use 'plagcheck serve' for the browser UI.", file=sys.stderr)
        return 1
    return 0


def cmd_mcp(args):
    from . import mcp

    return mcp.serve(args)


def build_parser():
    p = argparse.ArgumentParser(
        prog="plagcheck",
        description="Zero-dependency plagiarism checker — Turnitin-style, behemoth edition.",
    )
    p.add_argument("--version", action="version", version=f"plagcheck {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("identify", help="Identify file format (fast)")
    s.add_argument("path")
    s.add_argument("--json", action="store_true")
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(func=cmd_identify)

    s = sub.add_parser("inspect", help="Deep inspect with findings/forensics")
    s.add_argument("path")
    s.add_argument("--format", "-f", default=None)
    s.add_argument("--json", action="store_true")
    s.add_argument("--quiet", action="store_true")
    s.add_argument("--compact", action="store_true")
    s.set_defaults(func=cmd_inspect)

    s = sub.add_parser("list-formats", help="List supported format inspectors")
    s.add_argument("--json", action="store_true")
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(func=cmd_list_formats)

    s = sub.add_parser("index", help="Build a corpus index")
    s.add_argument("corpus")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_index)

    s = sub.add_parser("check", help="Check a document against a corpus")
    s.add_argument("file", nargs="?")
    s.add_argument("--text", dest="submission_text")
    s.add_argument("--corpus")
    s.add_argument("--index")
    s.add_argument("--url", action="append")
    s.add_argument("--k", type=int, default=5)
    s.add_argument("--w", type=int, default=4)
    s.add_argument("--min-run", type=int, dest="min_run")
    s.add_argument("--exclude-quotes", action="store_true")
    s.add_argument("--exclude-references", action="store_true")
    s.add_argument("--html")
    s.add_argument("--json-out")
    s.add_argument("--json", action="store_true", dest="json_report")
    s.add_argument("--text-report", action="store_true", dest="text_report")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("internal", help="Find repeated phrases within a document")
    s.add_argument("file", nargs="?")
    s.add_argument("--text", dest="submission_text")
    s.add_argument("--k", type=int, default=8)
    s.add_argument("--w", type=int, default=4)
    s.add_argument("--min-run", type=int, dest="min_run")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_internal)

    s = sub.add_parser("serve", help="Launch browser UI")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--corpus")
    s.add_argument("--index")
    s.set_defaults(func=cmd_serve)

    s = sub.add_parser("gui", help="Launch desktop UI")
    s.add_argument("--corpus")
    s.add_argument("--index")
    s.set_defaults(func=cmd_gui)

    s = sub.add_parser("mcp", help="Run MCP stdio server")
    s.set_defaults(func=cmd_mcp)

    return p


def build_corpus_index(corpus_dir, k=5, w=4, exclude_quotes=False, exclude_references=False):
    ci = indexmod.CorpusIndex()
    ci.build(corpus_dir)
    return ci


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        rc = args.func(args)
    except BrokenPipeError:
        rc = 0
    except Exception as e:
        print(f"plagcheck: {e}", file=sys.stderr)
        rc = 1
    sys.exit(rc)


if __name__ == "__main__":
    main()
