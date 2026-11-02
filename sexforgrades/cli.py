"""Command-line interface for SexForGrades - Students Liberation Engine."""

from __future__ import annotations

import argparse
import json
import sys

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
    ╔═╗╔═╗═╗ ╦  ╔═╗╔═╗╦═╗╔═╗╦═╗╔═╗╔╦╗╔═╗
    ╚═╗║╣ ╔╩╦╝  ╠╣ ║ ║╠╦╝║ ╦╠╦╝╠═╣ ║║╚═╗
    ╚═╝╚═╝╩ ╚═   ╚  ╚═╝╩╚═╚═╝╩╚═╩ ╩═╩╝╚═╝
        Students Liberation Engine • Zero-Dep • v{v}
"""


def _print(o):
    json.dump(o, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def cmd_identify(args):
    try:
        registry.identify(args.path)
        facts = registry.inspect_file(args.path)
    except Exception as e:
        print(f"sexforgrades: {e}", file=sys.stderr)
        return 1
    ins = {"schema": facts.get("schema"), "format": facts.get("format"), "confidence": facts.get("confidence"), "summary": facts.get("summary", ""), "file": facts.get("file")}
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
        print(f"sexforgrades: {e}", file=sys.stderr)
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
    if getattr(args, "submission_text", None):
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
        print(f"sexforgrades: gui unavailable: {e}", file=sys.stderr)
        print("Hint: use 'sexforgrades serve' for the browser UI.", file=sys.stderr)
        return 1
    return 0


def cmd_mcp(args):
    from . import mcp

    return mcp.serve(args)


def cmd_budget(args):
    from .policy import budget

    b = budget.BudgetAnalyzer()
    if args.input:
        b.load(args.input)
    res = b.analyze_education_vs_defense()
    if args.json:
        _print(res)
    else:
        print(res["summary"])
        if args.out:
            b.export_report(args.out)
            print(f"Wrote report to {args.out}")
    return 0


def cmd_petition(args):
    from .policy import petition

    pg = petition.PetitionGenerator()
    if args.type == "missing_marks" and args.institution:
        print(pg.generate_missing_marks_petition(args.institution))
    else:
        print(pg.generate_education_funding_petition())
    return 0


def cmd_rights(args):
    from .policy import civic

    r = civic.get_rights_summary()
    if args.json:
        _print(r)
    else:
        for k, v in r.items():
            print(f"{k}: {v}")
    return 0


def cmd_dashboard(args):
    from .dashboard import aggregator

    d = aggregator.AggregateDashboard()
    if args.input:
        d.load(args.input)
    res = d.export(args.out) if args.out else {"missing_marks": d.aggregate_missing_marks(), "science_suppression": d.aggregate_science_suppression()}
    if args.json or not args.out:
        _print(res)
    else:
        print(f"Wrote dashboard to {args.out}")
    return 0


def cmd_evidence_add(args):
    from .evidence import locker

    l = locker.EvidenceLocker(root=args.root)
    if args.consent:
        l.record_consent(args.consent, {"note": args.note or ""})
    files = args.file or []
    res = l.add_evidence(args.consent or "anon", args.desc or "", files=files, timeline_events=[])
    if args.json:
        _print(res)
    else:
        print(f"Added evidence entry {res['entry_id']}")
    return 0


def cmd_evidence_export(args):
    from .evidence import locker

    l = locker.EvidenceLocker(root=args.root)
    res = l.export_for_legal(args.consent, args.out)
    print(f"Exported {len(res)} entries to {args.out}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="sexforgrades", description="SexForGrades - Students Liberation Engine")
    p.add_argument("--version", action="version", version=f"sexforgrades {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("identify", help="Identify file format")
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

    s = sub.add_parser("list-formats", help="List format inspectors")
    s.add_argument("--json", action="store_true")
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(func=cmd_list_formats)

    s = sub.add_parser("index", help="Build evidence corpus index")
    s.add_argument("corpus")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_index)

    s = sub.add_parser("check", help="Audit document against evidence corpus")
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

    s = sub.add_parser("internal", help="Detect repeated patterns (cover-up letters)")
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

    s = sub.add_parser("budget", help="Analyze education vs defense budget")
    s.add_argument("--input")
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_budget)

    s = sub.add_parser("petition", help="Generate policy-based petition")
    s.add_argument("--type", choices=["education", "missing_marks"], default="education")
    s.add_argument("--institution")
    s.set_defaults(func=cmd_petition)

    s = sub.add_parser("rights", help="Civic rights summary")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_rights)

    s = sub.add_parser("dashboard", help="Aggregate dashboard (no individual targeting)")
    s.add_argument("--input", required=True)
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_dashboard)

    s = sub.add_parser("evidence-add", help="Add to consent-based evidence locker")
    s.add_argument("--consent")
    s.add_argument("--desc")
    s.add_argument("--note")
    s.add_argument("--file", action="append")
    s.add_argument("--root", default="./evidence_locker")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_evidence_add)

    s = sub.add_parser("evidence-export", help="Export for legal counsel with consent")
    s.add_argument("--consent", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--root", default="./evidence_locker")
    s.set_defaults(func=cmd_evidence_export)


    s = sub.add_parser("donor-report", help="Whistleblow on donors with conditions/conflicts of interest")
    s.add_argument("--donor", required=True)
    s.add_argument("--institution", required=True)
    s.add_argument("--details", required=True)
    s.add_argument("--condition", action="append")
    s.add_argument("--coi", action="append")
    s.add_argument("--file", action="append")
    s.add_argument("--root", default="./donor_watch")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_donor_report)

    s = sub.add_parser("donor-aggregate", help="Aggregate donor reports")
    s.add_argument("--root", default="./donor_watch")
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_donor_aggregate)


    s = sub.add_parser("campaign-create", help="Create student campaign (systems-focused)")
    s.add_argument("--name", required=True)
    s.add_argument("--demand", action="append")
    s.add_argument("--target", action="append")
    s.add_argument("--root", default="./campaigns")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_campaign_create)

    s = sub.add_parser("campaign-action", help="Add action to campaign")
    s.add_argument("--id", required=True)
    s.add_argument("--type", required=True)
    s.add_argument("--desc", required=True)
    s.add_argument("--root", default="./campaigns")
    s.set_defaults(func=cmd_campaign_action)

    s = sub.add_parser("mass-petition", help="Generate mass petition with additional demands")
    s.add_argument("--institution")
    s.add_argument("--demand", action="append")
    s.set_defaults(func=cmd_mass_petition)

    s = sub.add_parser("repression-defense", help="Safety checklist and legal referrals")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_repression_defense)


    s = sub.add_parser("handbook-inspect", help="Inspect student handbook for legal cracks")
    s.add_argument("file")
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_handbook_inspect)


    s = sub.add_parser("learn-create", help="Create self-paced learning path")
    s.add_argument("--course", required=True)
    s.add_argument("--module", action="append")
    s.add_argument("--root", default="./learning_paths")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_learn_create)

    s = sub.add_parser("learn-assess", help="Assess mastery")
    s.add_argument("--done", action="append")
    s.add_argument("--req", action="append")
    s.add_argument("--root", default="./learning_paths")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_learn_assess)

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
        print(f"sexforgrades: {e}", file=sys.stderr)
        rc = 1
    sys.exit(rc)


if __name__ == "__main__":
    main()


def cmd_donor_report(args):
    from .donors import whistle

    d = whistle.DonorTracker(root=args.root)
    files = args.file or []
    res = d.report(args.donor, args.institution, args.details, evidence_files=files, conditions=args.condition or [], conflict_of_interest=args.coi or [])
    if args.json:
        _print(res)
    else:
        print(f"Donor report {res['report_id']} recorded")
    return 0


def cmd_donor_aggregate(args):
    from .donors import whistle

    d = whistle.DonorTracker(root=args.root)
    res = d.aggregate()
    if args.json:
        _print(res)
    else:
        print(f"{res['count']} donor reports")
        if args.out:
            __import__('json').dump(res, open(args.out,'w'), indent=2)
            print(f"Wrote to {args.out}")
    return 0


def cmd_donor_report(args):
    from .donors import whistle
    d = whistle.DonorTracker(root=args.root)
    files = args.file or []
    res = d.report(args.donor, args.institution, args.details, evidence_files=files, conditions=args.condition or [], conflict_of_interest=args.coi or [])
    if args.json:
        _print(res)
    else:
        print(f"Donor report {res['report_id']} recorded")
    return 0


def cmd_donor_aggregate(args):
    from .donors import whistle
    d = whistle.DonorTracker(root=args.root)
    res = d.aggregate()
    if args.json:
        _print(res)
    else:
        print(f"{res['count']} donor reports")
        if args.out:
            import json
            open(args.out,'w').write(json.dumps(res, indent=2))
            print(f"Wrote to {args.out}")
    return 0


def cmd_campaign_create(args):
    from .organize import campaign
    c = campaign.Campaign(root=args.root)
    demands = args.demand or []
    res = c.create_campaign(args.name, demands, targets=args.target or [])
    if args.json:
        _print(res)
    else:
        print(f"Campaign {res['id']} created")
    return 0


def cmd_campaign_action(args):
    from .organize import campaign
    c = campaign.Campaign(root=args.root)
    res = c.add_action(args.id, args.type, args.desc)
    print(f"Added action to {res['id']}")
    return 0


def cmd_mass_petition(args):
    from .organize import campaign
    c = campaign.Campaign(root=args.root)
    demands = args.demand or []
    res = c.mass_petition(demands, args.institution)
    print(res)
    return 0


def cmd_repression_defense(args):
    from .organize import defense
    if args.json:
        _print({"checklist": defense.get_safety_checklist(), "referrals": defense.get_legal_referrals()})
    else:
        print("SAFETY CHECKLIST:")
        for i, item in enumerate(defense.get_safety_checklist(), 1):
            print(f"  {i}. {item}")
        print("\nLEGAL REFERRALS:")
        for k, v in defense.get_legal_referrals().items():
            print(f"  {v['name']}: {v['focus']}")
    return 0


def cmd_handbook_inspect(args):
    from .handbook import inspect
    h = inspect.HandbookInspector()
    res = h.inspect(args.file)
    if args.json:
        _print(res)
    else:
        print(f"Handbook: {res['file']}")
        print(f"Red flags: {res['count']}")
        for f in res['red_flags'][:20]:
            print(f"  - {f['reason']}: {f['snippet'][:100]}...")
        if args.out:
            h.report(res, args.out)
            print(f"Wrote report to {args.out}")
    return 0


def cmd_learn_create(args):
    from .learn import framework
    l = framework.LearningPath(root=args.root)
    modules = args.module or []
    res = l.create_path(args.course, modules)
    if args.json:
        _print(res)
    else:
        print(f"Learning path for {res['course']} created")
    return 0


def cmd_learn_assess(args):
    from .learn import framework
    l = framework.LearningPath(root=args.root)
    done = args.done or []
    req = args.req or []
    res = l.assess_mastery(done, req)
    if args.json:
        _print(res)
    else:
        print(f"Mastery: {res['mastery']}, Completion: {res['completion']:.1f}%")
    return 0
