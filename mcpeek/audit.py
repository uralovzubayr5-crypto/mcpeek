"""Static analysis of MCP tool definitions — no server needed to run the checks.

The runtime path (connecting over stdio with the `mcp` package) lives in
`connect.py`; this module is the part you can unit-test and run in CI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

RISKY_NAMES = ("file", "exec", "shell", "cmd", "http", "url", "sql", "query", "delete", "admin")
OVERRIDE_WORDS = ("ignore", "always", "override", "do not tell", "without asking")


@dataclass
class ToolFinding:
    name: str
    flags: list[str] = field(default_factory=list)

    def as_row(self) -> dict:
        return {"name": self.name, "flags": self.flags}


def risk_flags(tool: dict) -> list[str]:
    """Return a list of human-readable findings for one tool definition."""
    flags: list[str] = []
    schema = tool.get("inputSchema") or {}
    props = schema.get("properties") or {}

    if not props and not schema:
        flags.append("missing inputSchema — nothing to validate")

    for prop_name, spec in props.items():
        spec = spec or {}
        if spec.get("type") == "string" and not any(
            k in spec for k in ("maxLength", "enum", "pattern", "format")
        ):
            flags.append(f"unbounded string param: {prop_name}")
        if any(word in prop_name.lower() for word in RISKY_NAMES):
            flags.append(f"high-impact param: {prop_name}")

    description = (tool.get("description") or "").lower()
    for word in OVERRIDE_WORDS:
        if word in description:
            flags.append(f"description invites instruction override ({word!r})")
            break

    return flags


def audit(tools: list[dict]) -> list[ToolFinding]:
    """Audit a list of tool dicts (MCP `list_tools` shape or equivalent JSON)."""
    findings = [ToolFinding(name=t.get("name", "?"), flags=risk_flags(t)) for t in tools]
    # duplicate names are a surface-wide finding
    seen: dict[str, int] = {}
    for finding in findings:
        seen[finding.name] = seen.get(finding.name, 0) + 1
    for finding in findings:
        if seen[finding.name] > 1:
            finding.flags.append("duplicate tool name")
    return findings


def to_markdown(findings: list[ToolFinding]) -> str:
    rows = ["| tool | findings |", "|---|---|"]
    for finding in findings:
        cells = "<br>".join(finding.flags) if finding.flags else "ok"
        rows.append(f"| `{finding.name}` | {cells} |")
    return "\n".join(rows)


def to_json(findings: list[ToolFinding]) -> str:
    return json.dumps([f.as_row() for f in findings], indent=2)


def diff(old: list[ToolFinding], new: list[ToolFinding]) -> list[str]:
    """Report tool-surface changes between two audits."""
    old_map = {f.name: set(f.flags) for f in old}
    new_map = {f.name: set(f.flags) for f in new}
    out: list[str] = []
    for name in sorted(new_map.keys() - old_map.keys()):
        out.append(f"+ new tool: {name}")
    for name in sorted(old_map.keys() - new_map.keys()):
        out.append(f"- removed tool: {name}")
    for name in sorted(old_map.keys() & new_map.keys()):
        added = new_map[name] - old_map[name]
        removed = old_map[name] - new_map[name]
        for flag in sorted(added):
            out.append(f"~ {name}: + {flag}")
        for flag in sorted(removed):
            out.append(f"~ {name}: - {flag}")
    return out
