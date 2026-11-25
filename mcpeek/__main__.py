"""CLI: mcpeek audit -- <server command> | mcpeek audit --json | mcpeek diff a.json b.json"""

from __future__ import annotations

import argparse
import json
import sys

from .audit import ToolFinding, diff, to_json, to_markdown
from .connect import audit_server


def _load(path: str) -> list[ToolFinding]:
    raw = json.load(open(path, encoding="utf-8"))
    return [ToolFinding(name=row["name"], flags=row.get("flags", [])) for row in raw]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcpeek", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    audit_p = sub.add_parser("audit", help="audit a stdio MCP server")
    audit_p.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    audit_p.add_argument("server", nargs=argparse.REMAINDER, help="-- command args…")

    diff_p = sub.add_parser("diff", help="diff two saved audits")
    diff_p.add_argument("old")
    diff_p.add_argument("new")

    args = parser.parse_args(argv)

    if args.cmd == "audit":
        server = [part for part in args.server if part != "--"]
        if not server:
            parser.error("give the server command after --, e.g. mcpeek audit -- python server.py")
        findings = audit_server(server[0], server[1:])
        print(to_json(findings) if args.json else to_markdown(findings))
        return 1 if any(f.flags for f in findings) else 0

    if args.cmd == "diff":
        changes = diff(_load(args.old), _load(args.new))
        print("\n".join(changes) if changes else "no tool-surface changes")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
