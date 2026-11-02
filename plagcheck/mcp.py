"""MCP stdio server for plagcheck."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import __version__
from . import extract
from . import index as indexmod
from . import compare
from .core import registry

try:
    from . import formats  # noqa
except Exception:
    pass


def _resp(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        msg["error"] = {"code": -32000, "message": str(error)}
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def serve(args=None):
    tools = [
        {
            "name": "plagcheck_identify",
            "description": "Identify file format",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
        {
            "name": "plagcheck_inspect",
            "description": "Deep inspect file with findings/forensics",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "format": {"type": "string"}},
                "required": ["path"],
            },
        },
        {
            "name": "plagcheck_list_formats",
            "description": "List format inspectors",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "plagcheck_index_corpus",
            "description": "Build corpus index (returns index path)",
            "inputSchema": {
                "type": "object",
                "properties": {"corpus": {"type": "string"}, "out": {"type": "string"}},
                "required": ["corpus", "out"],
            },
        },
        {
            "name": "plagcheck_check",
            "description": "Check submission against corpus/index",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "text": {"type": "string"},
                    "corpus": {"type": "string"},
                    "index": {"type": "string"},
                    "k": {"type": "integer"},
                    "w": {"type": "integer"},
                    "urls": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    ]

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        method = req.get("method")
        id_ = req.get("id")
        if method == "initialize":
            _resp(
                id_,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "plagcheck-mcp", "version": __version__},
                },
            )
            continue
        if method == "tools/list":
            _resp(id_, {"tools": tools})
            continue
        if method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            try:
                if name == "plagcheck_identify":
                    env = registry.inspect_file(args["path"])
                    _resp(id_, {"content": [{"type": "text", "text": json.dumps(env)}]})
                    continue
                if name == "plagcheck_inspect":
                    env = registry.inspect_file(args["path"], fmt_name=args.get("format"))
                    _resp(id_, {"content": [{"type": "text", "text": json.dumps(env)}]})
                    continue
                if name == "plagcheck_list_formats":
                    fmts = registry.list_formats()
                    _resp(id_, {"content": [{"type": "text", "text": json.dumps(fmts)}]})
                    continue
                if name == "plagcheck_index_corpus":
                    ci = indexmod.CorpusIndex()
                    ci.build(args["corpus"])
                    ci.save(args["out"])
                    _resp(
                        id_,
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps({"indexed": len(ci.documents), "out": args["out"]}),
                                }
                            ]
                        },
                    )
                    continue
                if name == "plagcheck_check":
                    ci = None
                    if args.get("index"):
                        ci = indexmod.CorpusIndex.load(args["index"])
                    elif args.get("corpus"):
                        ci = indexmod.CorpusIndex()
                        ci.build(args["corpus"])
                    else:
                        ci = indexmod.CorpusIndex()
                    if args.get("text"):
                        sub = args["text"]
                    elif args.get("file"):
                        sub = extract.extract_text(args["file"])
                    else:
                        raise ValueError("need text or file")
                    res = compare.analyze(
                        sub,
                        ci,
                        k=args.get("k", 5),
                        w=args.get("w", 4),
                        urls=args.get("urls") or [],
                    )
                    _resp(id_, {"content": [{"type": "text", "text": json.dumps(res.to_dict())}]})
                    continue
                _resp(id_, error=f"unknown tool: {name}")
            except Exception as e:
                _resp(id_, error=e)
            continue
        # ignore others
    return 0
